from asyncio import Event
import functools
import inspect
import time
import types


class Step:
    @staticmethod
    def with_name(name):
        return functools.partial(Step, name=name)

    @staticmethod
    def of(outputs):
        return functools.partial(Step, of=outputs)

    @staticmethod
    def on(inputs):
        return functools.partial(Step, on=inputs)

    def __init__(self, func, of, on=None, name=None):
        self._func = func
        self._name = name or func.__name__
        self._inputs = on or tuple(inspect.signature(func).parameters.keys())
        self._outputs = of or inspect.signature(func).return_annotation
        # TODO check if arguments OK
        self._started = Event()
        self._finished = Event()
        self._completed = Event()
        self._errored = Event()

    def clone(self):
        return Step(self._func, self._name, self._inputs, self._outputs)

    @property
    def name(self):
        return self._name

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        if isinstance(self._outputs, str):
            return [self._outputs]
        else:
            return self._outputs

    _last_started = None
    _last_started_pc = None
    _last_finished = None
    _last_finished_pc = None
    _last_profile_duration = None
    _last_input = None
    _last_output = None
    _last_error = None
    _started = None
    _finished = None
    _completed = None
    _errored = None

    def _clean(self):
        self._last_started = None
        self._last_started_pc = None
        self._last_finished = None
        self._last_finished_pc = None
        self._last_profile_duration = None
        self._last_input = None
        self._last_output = None
        self._last_error = None
        self._started.clear()
        self._finished.clear()
        self._completed.clear()
        self._errored.clear()

    def _load(self, state):
        # TODO check if in right state
        self._last_input = [state[inp] for inp in self.inputs]

    def _run(self):
        # TODO check if in right state
        self._started.set()
        self._last_started = time.time()
        self._last_started_pc = time.perf_counter()
        started = time.process_time()
        try:
            try:
                self._last_output = self._func(*self._last_input)
            except BaseException as e:
                self._last_error = e
                raise
            finally:
                self._last_profile_duration = time.process_time() - started
                self._last_finished_pc = time.perf_counter()
                self._last_finished = time.time()
            self._completed.set()
        except BaseException as e:
            self._errored.set()
            raise
        finally:
            self._finished.set()

    def _save(self, state):
        # TODO check if in right state
        if isinstance(self._outputs, str):
            state[self._outputs] = self._last_output
        elif isinstance(self._last_output, list) or isinstance(self._last_output, tuple):
            for k, v in zip(self.outputs, self._last_output):
                state[k] = v
        elif isinstance(self._last_output, dict):
            for k, v in self._last_output.items():
                state[k] = v
        else:
            raise RuntimeError(f"Step {self.name} returned of unexpected type: {type(self._last_output)}")

    def run_on(self, state):
        self._clean()
        self._load(state)
        self._run()
        self._save(state)


class Pipeline:
    steps = []
    _sealed = False

    def add_step(self, step=None, *args, **kwargs):
        if step is None:
            return lambda _step: self.add_step(_step, *args, **kwargs)
        if isinstance(step, Step):
            self.steps.append(step)
            return step
        if isinstance(step, types.FunctionType):
            return self.add_step(Step(step, *args, **kwargs))
        else:
            raise RuntimeError(f"Invalid step type: {type(step)}")

    def remove_step(self, step, index=0):
        if isinstance(step, Step):
            step = step.name

        for i in range(len(self.steps)):
            if isinstance(step, Step):
                if self.steps[i] != step:
                    continue
            elif isinstance(step, str):
                if self.steps[i].name != step:
                    continue
            else:
                raise ValueError(f"step argument is of unexpected type ({type(step)})")

            if index == 0:
                del self.steps[i]
                return
            else:
                index = index - 1

        raise IndexError(f'Step {step} was requested {index + 1} more time for deletion')

    def seal_steps(self):
        self._sealed = True

    def clone(self):
        clone = Pipeline()
        for step in self.steps:
            clone.steps.append(step)
        if self.sealed:
            clone.seal_steps()
        return clone

    def run(self, outputs, cb=None):
        state = {}

        for step_index, step in enumerate(self.steps):
            if cb is not None:
                cb(step, pipeline=self, state=state, done=False, error=None, step_index=step_index)
            else:
                print(f"[{step_index + 1}/{len(self.steps)}] Executing step {step.name}...", end="")

            try:
                step.run_on(state)
            except Exception as e:
                if cb is not None:
                    cb(step, pipeline=self, state=state, done=False, error=e, step_index=step_index)
                raise

            if cb is not None:
                cb(step, pipeline=self, state=state, done=True, error=None, step_index=step_index)
            else:
                print(f" done (took {step._last_profile_duration:.3}s)")

        return [state[out] for out in outputs]

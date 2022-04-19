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

    def __init__(self, func, of, on=None, name=None, details=None):
        self._func = func
        self._name = name or func.__name__
        self._inputs = on or tuple(inspect.signature(func).parameters.keys())
        self._outputs = of or inspect.signature(func).return_annotation
        # TODO check if arguments OK
        self._last_started = None
        self._last_started_pc = None
        self._last_finished = None
        self._last_finished_pc = None
        self._last_profile_duration = None
        self._last_input = None
        self._last_output = None
        self._last_error = None
        self._started = Event()
        self._finished = Event()
        self._completed = Event()
        self._errored = Event()
        self.details = details

    def clone(self):
        return Step(self._func, self._name, self._inputs, self._outputs)

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

    @property
    def last_input(self):
        return dict(zip(self.inputs, self._last_input))

    @property
    def last_output(self):
        if isinstance(self._last_output, dict):
            return self._last_output
        elif isinstance(self._outputs, str):
            return {self._outputs: self._last_output}
        else:
            return dict(zip(self.outputs, self._last_output))

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
    def __init__(self):
        self.state = None
        self.steps = []
        self._sealed = False

    def add_step(self, step=None, *args, **kwargs):
        if step is None:
            return lambda _step: self.add_step(_step, *args, **kwargs)
        if isinstance(step, Step):
            self.steps.append(step)
            return step
        if isinstance(step, types.FunctionType) or isinstance(step, functools.partial):
            return self.add_step(Step(step, *args, **kwargs))
        else:
            raise RuntimeError(f"Invalid step type: {type(step)}")

    def remove_step(self, step, index=0):
        i = self.find_step(step, index, return_index=True)
        del self.steps[i]

    def find_step(self, step, index=0, return_index=False):
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
                if return_index:
                    return i
                else:
                    return self.steps[i]
            else:
                index = index - 1

        raise IndexError(f'Step {step} was requested to be found {index + 1} more time')

    def seal_steps(self):
        self._sealed = True

    def clone(self):
        clone = Pipeline()
        for step in self.steps:
            clone.steps.append(step)
        if self.sealed:
            clone.seal_steps()
        return clone

    def _clean(self):
        for step in self.steps:
            step._clean()
        self.state = None

    def _hook(self, hook, *args, **kwargs):
        if hook is not None:
            hook(*args, **kwargs)
        else:
            self._default_hook(*args, **kwargs)

    def _default_hook(self, step, finished, error, step_index, *args, **kwargs):
        if not finished:
            print(f"[{step_index + 1}/{len(self.steps)}] Executing step {step.name}...", end="")
        elif error is not None:
            print(f" ERROR")
        else:
            print(f" done (took {step._last_profile_duration:.3}s)")

    def run(self, outputs=[], hook=None):
        if self.state is not None:
            raise RuntimeError("State not clean")

        self.state = {}

        for step_index, step in enumerate(self.steps):
            self._hook(hook, step, pipeline=self, state=self.state, finished=False, completed=False, error=None, step_index=step_index)

            try:
                step.run_on(self.state)
            except Exception as e:
                self._hook(hook, step, pipeline=self, state=self.state, finished=True, completed=False, error=e, step_index=step_index)
                raise

            self._hook(hook, step, pipeline=self, state=self.state, finished=True, completed=True, error=None, step_index=step_index)

        return [self.state[out] for out in outputs]

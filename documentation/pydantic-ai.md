# agents
## Introduction

Agents are PydanticAI's primary interface for interacting with LLMs.

In some use cases a single Agent will control an entire application or component, but multiple agents can also interact to embody more complex workflows.

The [`Agent`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent) class has full API documentation, but conceptually you can think of an agent as a container for:

In typing terms, agents are generic in their dependency and result types, e.g., an agent which required dependencies of type `Foobar` and returned results of type `list[str]` would have type `Agent[Foobar, list[str]]`. In practice, you shouldn't need to care about this, it should just mean your IDE can tell you when you have the right type, and if you choose to use [static type checking](https://ai.pydantic.dev/agents/#static-type-checking) it should work well with PydanticAI.

Here's a toy example of an agent that simulates a roulette wheel:

roulette\_wheel.py

```python
from pydantic_ai import Agent, RunContext

roulette_agent = Agent(  
    'openai:gpt-4o',
    deps_type=int,
    result_type=bool,
    system_prompt=(
        'Use the \`roulette_wheel\` function to see if the '
        'customer has won based on the number they provide.'
    ),
)

@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:  
    """check if the square is a winner"""
    return 'winner' if square == ctx.deps else 'loser'

# Run the agent
success_number = 18  
result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
print(result.data)  
#> True

result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
print(result.data)
#> False
```

Agents are designed for reuse, like FastAPI Apps

Agents are intended to be instantiated once (frequently as module globals) and reused throughout your application, similar to a small [FastAPI](https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI) app or an [APIRouter](https://fastapi.tiangolo.com/reference/apirouter/#fastapi.APIRouter).

## Running Agents

There are three ways to run an agent:

1. [`agent.run()`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run) — a coroutine which returns a [`RunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult) containing a completed response
2. [`agent.run_sync()`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run_sync) — a plain, synchronous function which returns a [`RunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult) containing a completed response (internally, this just calls `loop.run_until_complete(self.run())`)
3. [`agent.run_stream()`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run_stream) — a coroutine which returns a [`StreamedRunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.StreamedRunResult), which contains methods to stream a response as an async iterable

Here's a simple example demonstrating all three:

run\_agent.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')

result_sync = agent.run_sync('What is the capital of Italy?')
print(result_sync.data)
#> Rome

async def main():
    result = await agent.run('What is the capital of France?')
    print(result.data)
    #> Paris

    async with agent.run_stream('What is the capital of the UK?') as response:
        print(await response.get_data())
        #> London
```

*(This example is complete, it can be run "as is")*

You can also pass messages from previous runs to continue a conversation or provide context, as described in [Messages and Chat History](https://ai.pydantic.dev/message-history/).

jupyter notebooks

If you're running `pydantic-ai` in a jupyter notebook, you might consider using [`nest-asyncio`](https://pypi.org/project/nest-asyncio/) to manage conflicts between event loops that occur between jupyter's event loops and `pydantic-ai`'s.

Before you execute any agent runs, do the following:

```python
import nest_asyncio

nest_asyncio.apply()
```

### Additional Configuration

#### Usage Limits

PydanticAI offers a [`settings.UsageLimits`](https://ai.pydantic.dev/api/settings/#pydantic_ai.settings.UsageLimits) structure to help you limit your usage (tokens and/or requests) on model runs.

You can apply these settings by passing the `usage_limits` argument to the `run{_sync,_stream}` functions.

Consider the following example, where we limit the number of response tokens:

```py
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.settings import UsageLimits

agent = Agent('claude-3-5-sonnet-latest')

result_sync = agent.run_sync(
    'What is the capital of Italy? Answer with just the city.',
    usage_limits=UsageLimits(response_tokens_limit=10),
)
print(result_sync.data)
#> Rome
print(result_sync.usage())
"""
Usage(requests=1, request_tokens=62, response_tokens=1, total_tokens=63, details=None)
"""

try:
    result_sync = agent.run_sync(
        'What is the capital of Italy? Answer with a paragraph.',
        usage_limits=UsageLimits(response_tokens_limit=10),
    )
except UsageLimitExceeded as e:
    print(e)
    #> Exceeded the response_tokens_limit of 10 (response_tokens=32)
```

Restricting the number of requests can be useful in preventing infinite loops or excessive tool calling:

```py
from typing_extensions import TypedDict

from pydantic_ai import Agent, ModelRetry
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.settings import UsageLimits

class NeverResultType(TypedDict):
    """
    Never ever coerce data to this type.
    """

    never_use_this: str

agent = Agent(
    'claude-3-5-sonnet-latest',
    result_type=NeverResultType,
    system_prompt='Any time you get a response, call the \`infinite_retry_tool\` to produce another response.',
)

@agent.tool_plain(retries=5)  
def infinite_retry_tool() -> int:
    raise ModelRetry('Please try again.')

try:
    result_sync = agent.run_sync(
        'Begin infinite retry loop!', usage_limits=UsageLimits(request_limit=3)  
    )
except UsageLimitExceeded as e:
    print(e)
    #> The next request would exceed the request_limit of 3
```

Note

This is especially relevant if you're registered a lot of tools, `request_limit` can be used to prevent the model from choosing to make too many of these calls.

#### Model (Run) Settings

PydanticAI offers a [`settings.ModelSettings`](https://ai.pydantic.dev/api/settings/#pydantic_ai.settings.ModelSettings) structure to help you fine tune your requests. This structure allows you to configure common parameters that influence the model's behavior, such as `temperature`, `max_tokens`, `timeout`, and more.

There are two ways to apply these settings: 1. Passing to `run{_sync,_stream}` functions via the `model_settings` argument. This allows for fine-tuning on a per-request basis. 2. Setting during [`Agent`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent) initialization via the `model_settings` argument. These settings will be applied by default to all subsequent run calls using said agent. However, `model_settings` provided during a specific run call will override the agent's default settings.

For example, if you'd like to set the `temperature` setting to `0.0` to ensure less random behavior, you can do the following:

```py
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')

result_sync = agent.run_sync(
    'What is the capital of Italy?', model_settings={'temperature': 0.0}
)
print(result_sync.data)
#> Rome
```

## Runs vs. Conversations

An agent **run** might represent an entire conversation — there's no limit to how many messages can be exchanged in a single run. However, a **conversation** might also be composed of multiple runs, especially if you need to maintain state between separate interactions or API calls.

Here's an example of a conversation comprised of multiple runs:

conversation\_example.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')

# First run
result1 = agent.run_sync('Who was Albert Einstein?')
print(result1.data)
#> Albert Einstein was a German-born theoretical physicist.

# Second run, passing previous messages
result2 = agent.run_sync(
    'What was his most famous equation?',
    message_history=result1.new_messages(),  
)
print(result2.data)
#> Albert Einstein's most famous equation is (E = mc^2).
```

*(This example is complete, it can be run "as is")*

## Type safe by design

PydanticAI is designed to work well with static type checkers, like mypy and pyright.

Typing is (somewhat) optional

PydanticAI is designed to make type checking as useful as possible for you if you choose to use it, but you don't have to use types everywhere all the time.

That said, because PydanticAI uses Pydantic, and Pydantic uses type hints as the definition for schema and validation, some types (specifically type hints on parameters to tools, and the `result_type` arguments to [`Agent`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent)) are used at runtime.

We (the library developers) have messed up if type hints are confusing you more than helping you, if you find this, please create an [issue](https://github.com/pydantic/pydantic-ai/issues) explaining what's annoying you!

In particular, agents are generic in both the type of their dependencies and the type of results they return, so you can use the type hints to ensure you're using the right types.

Consider the following script with type mistakes:

type\_mistakes.py

```python
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

@dataclass
class User:
    name: str

agent = Agent(
    'test',
    deps_type=User,  
    result_type=bool,
)

@agent.system_prompt
def add_user_name(ctx: RunContext[str]) -> str:  
    return f"The user's name is {ctx.deps}."

def foobar(x: bytes) -> None:
    pass

result = agent.run_sync('Does their name start with "A"?', deps=User('Anne'))
foobar(result.data)  
```

Running `mypy` on this will give the following output:

```bash
➤ uv run mypy type_mistakes.py
type_mistakes.py:18: error: Argument 1 to "system_prompt" of "Agent" has incompatible type "Callable[[RunContext[str]], str]"; expected "Callable[[RunContext[User]], str]"  [arg-type]
type_mistakes.py:28: error: Argument 1 to "foobar" has incompatible type "bool"; expected "bytes"  [arg-type]
Found 2 errors in 1 file (checked 1 source file)
```

Running `pyright` would identify the same issues.

## System Prompts

System prompts might seem simple at first glance since they're just strings (or sequences of strings that are concatenated), but crafting the right system prompt is key to getting the model to behave as you want.

Generally, system prompts fall into two categories:

1. **Static system prompts**: These are known when writing the code and can be defined via the `system_prompt` parameter of the [`Agent` constructor](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.__init__).
2. **Dynamic system prompts**: These depend in some way on context that isn't known until runtime, and should be defined via functions decorated with [`@agent.system_prompt`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.system_prompt).

You can add both to a single agent; they're appended in the order they're defined at runtime.

Here's an example using both types of system prompts:

system\_prompts.py

```python
from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-4o',
    deps_type=str,  
    system_prompt="Use the customer's name while replying to them.",  
)

@agent.system_prompt  
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."

@agent.system_prompt
def add_the_date() -> str:  
    return f'The date is {date.today()}.'

result = agent.run_sync('What is the date?', deps='Frank')
print(result.data)
#> Hello Frank, the date today is 2032-01-02.
```

*(This example is complete, it can be run "as is")*

## Reflection and self-correction

Validation errors from both function tool parameter validation and [structured result validation](https://ai.pydantic.dev/results/#structured-result-validation) can be passed back to the model with a request to retry.

You can also raise [`ModelRetry`](https://ai.pydantic.dev/api/exceptions/#pydantic_ai.exceptions.ModelRetry) from within a [tool](https://ai.pydantic.dev/tools/) or [result validator function](https://ai.pydantic.dev/results/#result-validators-functions) to tell the model it should retry generating a response.

- The default retry count is **1** but can be altered for the [entire agent](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.__init__), a [specific tool](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.tool), or a [result validator](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.__init__).
- You can access the current retry count from within a tool or result validator via [`ctx.retry`](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.RunContext).

Here's an example:

tool\_retry.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry

from fake_database import DatabaseConn

class ChatResult(BaseModel):
    user_id: int
    message: str

agent = Agent(
    'openai:gpt-4o',
    deps_type=DatabaseConn,
    result_type=ChatResult,
)

@agent.tool(retries=2)
def get_user_by_name(ctx: RunContext[DatabaseConn], name: str) -> int:
    """Get a user's ID from their full name."""
    print(name)
    #> John
    #> John Doe
    user_id = ctx.deps.users.get(name=name)
    if user_id is None:
        raise ModelRetry(
            f'No user found with name {name!r}, remember to provide their full name'
        )
    return user_id

result = agent.run_sync(
    'Send a message to John Doe asking for coffee next week', deps=DatabaseConn()
)
print(result.data)
"""
user_id=123 message='Hello John, would you be free for coffee sometime next week? Let me know what works for you!'
"""
```

## Model errors

If models behave unexpectedly (e.g., the retry limit is exceeded, or their API returns `503`), agent runs will raise [`UnexpectedModelBehavior`](https://ai.pydantic.dev/api/exceptions/#pydantic_ai.exceptions.UnexpectedModelBehavior).

In these cases, [`agent.last_run_messages`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.last_run_messages) can be used to access the messages exchanged during the run to help diagnose the issue.

```python
from pydantic_ai import Agent, ModelRetry, UnexpectedModelBehavior

agent = Agent('openai:gpt-4o')

@agent.tool_plain
def calc_volume(size: int) -> int:  # (1)!
    if size == 42:
        return size**3
    else:
        raise ModelRetry('Please try again.')

try:
    result = agent.run_sync('Please get me the volume of a box with size 6.')
except UnexpectedModelBehavior as e:
    print('An error occurred:', e)
    #> An error occurred: Tool exceeded max retries count of 1
    print('cause:', repr(e.__cause__))
    #> cause: ModelRetry('Please try again.')
    print('messages:', agent.last_run_messages)
    """
    messages:
    [
        ModelRequest(
            parts=[
                UserPromptPart(
                    content='Please get me the volume of a box with size 6.',
                    timestamp=datetime.datetime(...),
                    part_kind='user-prompt',
                )
            ],
            kind='request',
        ),
        ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='calc_volume',
                    args=ArgsDict(args_dict={'size': 6}),
                    tool_call_id=None,
                    part_kind='tool-call',
                )
            ],
            timestamp=datetime.datetime(...),
            kind='response',
        ),
        ModelRequest(
            parts=[
                RetryPromptPart(
                    content='Please try again.',
                    tool_name='calc_volume',
                    tool_call_id=None,
                    timestamp=datetime.datetime(...),
                    part_kind='retry-prompt',
                )
            ],
            kind='request',
        ),
        ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='calc_volume',
                    args=ArgsDict(args_dict={'size': 6}),
                    tool_call_id=None,
                    part_kind='tool-call',
                )
            ],
            timestamp=datetime.datetime(...),
            kind='response',
        ),
    ]
    """
else:
    print(result.data)
```

1\. Define a tool that will raise `ModelRetry` repeatedly in this case.

*(This example is complete, it can be run "as is")*

# debugging and monitoring
Version Notice

This documentation is ahead of the last release by **10** commits. You may see documentation for features not yet supported in the latest release [v0.0.14 2024-12-19](https://github.com/pydantic/pydantic-ai/releases/tag/v0.0.14).

Applications that use LLMs have some challenges that are well known and understood: LLMs are **slow**, **unreliable** and **expensive**.

These applications also have some challenges that most developers have encountered much less often: LLMs are **fickle** and **non-deterministic**. Subtle changes in a prompt can completely change a model's performance, and there's no `EXPLAIN` query you can run to understand why.

Warning

From a software engineers point of view, you can think of LLMs as the worst database you've ever heard of, but worse.

If LLMs weren't so bloody useful, we'd never touch them.

To build successful applications with LLMs, we need new tools to understand both model performance, and the behavior of applications that rely on them.

LLM Observability tools that just let you understand how your model is performing are useless: making API calls to an LLM is easy, it's building that into an application that's hard.

## Pydantic Logfire

[Pydantic Logfire](https://pydantic.dev/logfire) is an observability platform developed by the team who created and maintain Pydantic and PydanticAI. Logfire aims to let you understand your entire application: Gen AI, classic predictive AI, HTTP traffic, database queries and everything else a modern application needs.

Pydantic Logfire is a commercial product

Logfire is a commercially supported, hosted platform with an extremely generous and perpetual [free tier](https://pydantic.dev/pricing/). You can sign up and start using Logfire in a couple of minutes.

PydanticAI has built-in (but optional) support for Logfire via the [`logfire-api`](https://github.com/pydantic/logfire/tree/main/logfire-api) no-op package.

That means if the `logfire` package is installed and configured, detailed information about agent runs is sent to Logfire. But if the `logfire` package is not installed, there's virtually no overhead and nothing is sent.

Here's an example showing details of running the [Weather Agent](https://ai.pydantic.dev/examples/weather-agent/) in Logfire:

[![Weather Agent Logfire](https://ai.pydantic.dev/img/logfire-weather-agent.png)](https://ai.pydantic.dev/img/logfire-weather-agent.png)

## Using Logfire

To use logfire, you'll need a logfire [account](https://logfire.pydantic.dev/), and logfire installed:

```
pip install 'pydantic-ai[logfire]'
```

```
uv add 'pydantic-ai[logfire]'
```

Then authenticate your local environment with logfire:

And configure a project to send data to:

```
uv run logfire projects new
```

(Or use an existing project with `logfire projects use`)

The last step is to add logfire to your code:

adding\_logfire.py

```python
import logfire

logfire.configure()
```

The [logfire documentation](https://logfire.pydantic.dev/docs/) has more details on how to use logfire, including how to instrument other libraries like Pydantic, HTTPX and FastAPI.

Since Logfire is build on [OpenTelemetry](https://opentelemetry.io/), you can use the Logfire Python SDK to send data to any OpenTelemetry collector.

Once you have logfire set up, there are two primary ways it can help you understand your application:

- **Debugging** — Using the live view to see what's happening in your application in real-time.
- **Monitoring** — Using SQL and dashboards to observe the behavior of your application, Logfire is effectively a SQL database that stores information about how your application is running.

### Debugging

To demonstrate how Logfire can let you visualise the flow of a PydanticAI run, here's the view you get from Logfire while running the [chat app examples](https://ai.pydantic.dev/examples/chat-app/):

### Monitoring Performance

We can also query data with SQL in Logfire to monitor the performance of an application. Here's a real world example of using Logfire to monitor PydanticAI runs inside Logfire itself:

[![Logfire monitoring PydanticAI](https://ai.pydantic.dev/img/logfire-monitoring-pydanticai.png)](https://ai.pydantic.dev/img/logfire-monitoring-pydanticai.png)

# dependencies
Version Notice

This documentation is ahead of the last release by **10** commits. You may see documentation for features not yet supported in the latest release [v0.0.14 2024-12-19](https://github.com/pydantic/pydantic-ai/releases/tag/v0.0.14).

PydanticAI uses a dependency injection system to provide data and services to your agent's [system prompts](https://ai.pydantic.dev/agents/#system-prompts), [tools](https://ai.pydantic.dev/tools/) and [result validators](https://ai.pydantic.dev/results/#result-validators-functions).

Matching PydanticAI's design philosophy, our dependency system tries to use existing best practice in Python development rather than inventing esoteric "magic", this should make dependencies type-safe, understandable easier to test and ultimately easier to deploy in production.

## Defining Dependencies

Dependencies can be any python type. While in simple cases you might be able to pass a single object as a dependency (e.g. an HTTP connection), [dataclasses](https://docs.python.org/3/library/dataclasses.html#module-dataclasses) are generally a convenient container when your dependencies included multiple objects.

Here's an example of defining an agent that requires dependencies.

(**Note:** dependencies aren't actually used in this example, see [Accessing Dependencies](https://ai.pydantic.dev/dependencies/#accessing-dependencies) below)

unused\_dependencies.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent

@dataclass
class MyDeps:  
    api_key: str
    http_client: httpx.AsyncClient

agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,  
)

async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run(
            'Tell me a joke.',
            deps=deps,  
        )
        print(result.data)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

*(This example is complete, it can be run "as is")*

## Accessing Dependencies

Dependencies are accessed through the [`RunContext`](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.RunContext) type, this should be the first parameter of system prompt functions etc.

system\_prompt\_dependencies.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext

@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient

agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,
)

@agent.system_prompt  
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  
    response = await ctx.deps.http_client.get(  
        'https://example.com',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},  
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'

async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.data)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

*(This example is complete, it can be run "as is")*

### Asynchronous vs. Synchronous dependencies

[System prompt functions](https://ai.pydantic.dev/agents/#system-prompts), [function tools](https://ai.pydantic.dev/tools/) and [result validators](https://ai.pydantic.dev/results/#result-validators-functions) are all run in the async context of an agent run.

If these functions are not coroutines (e.g. `async def`) they are called with [`run_in_executor`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor) in a thread pool, it's therefore marginally preferable to use `async` methods where dependencies perform IO, although synchronous dependencies should work fine too.

`run` vs. `run_sync` and Asynchronous vs. Synchronous dependencies

Whether you use synchronous or asynchronous dependencies, is completely independent of whether you use `run` or `run_sync` — `run_sync` is just a wrapper around `run` and agents are always run in an async context.

Here's the same example as above, but with a synchronous dependency:

sync\_dependencies.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext

@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.Client  

agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,
)

@agent.system_prompt
def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  
    response = ctx.deps.http_client.get(
        'https://example.com', headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'

async def main():
    deps = MyDeps('foobar', httpx.Client())
    result = await agent.run(
        'Tell me a joke.',
        deps=deps,
    )
    print(result.data)
    #> Did you hear about the toothpaste scandal? They called it Colgate.
```

*(This example is complete, it can be run "as is")*

## Full Example

As well as system prompts, dependencies can be used in [tools](https://ai.pydantic.dev/tools/) and [result validators](https://ai.pydantic.dev/results/#result-validators-functions).

full\_example.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, ModelRetry, RunContext

@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient

agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,
)

@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    response = await ctx.deps.http_client.get('https://example.com')
    response.raise_for_status()
    return f'Prompt: {response.text}'

@agent.tool  
async def get_joke_material(ctx: RunContext[MyDeps], subject: str) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com#jokes',
        params={'subject': subject},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    return response.text

@agent.result_validator  
async def validate_result(ctx: RunContext[MyDeps], final_response: str) -> str:
    response = await ctx.deps.http_client.post(
        'https://example.com#validate',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
        params={'query': final_response},
    )
    if response.status_code == 400:
        raise ModelRetry(f'invalid response: {response.text}')
    response.raise_for_status()
    return final_response

async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.data)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

*(This example is complete, it can be run "as is")*

## Overriding Dependencies

When testing agents, it's useful to be able to customise dependencies.

While this can sometimes be done by calling the agent directly within unit tests, we can also override dependencies while calling application code which in turn calls the agent.

This is done via the [`override`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.override) method on the agent.

joke\_app.py

```python
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext

@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient

    async def system_prompt_factory(self) -> str:  
        response = await self.http_client.get('https://example.com')
        response.raise_for_status()
        return f'Prompt: {response.text}'

joke_agent = Agent('openai:gpt-4o', deps_type=MyDeps)

@joke_agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    return await ctx.deps.system_prompt_factory()  

async def application_code(prompt: str) -> str:  
    ...
    ...
    # now deep within application code we call our agent
    async with httpx.AsyncClient() as client:
        app_deps = MyDeps('foobar', client)
        result = await joke_agent.run(prompt, deps=app_deps)  
    return result.data
```

test\_joke\_app.py

```python
from joke_app import MyDeps, application_code, joke_agent

class TestMyDeps(MyDeps):  
    async def system_prompt_factory(self) -> str:
        return 'test prompt'

async def test_application_code():
    test_deps = TestMyDeps('test_key', None)  
    with joke_agent.override(deps=test_deps):  
        joke = await application_code('Tell me a joke.')  
    assert joke.startswith('Did you hear about the toothpaste scandal?')
```

## Agents as dependencies of other Agents

Since dependencies can be any python type, and agents are just python objects, agents can be dependencies of other agents.

agents\_as\_dependencies.py

```python
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

@dataclass
class MyDeps:
    factory_agent: Agent[None, list[str]]

joke_agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,
    system_prompt=(
        'Use the "joke_factory" to generate some jokes, then choose the best. '
        'You must return just a single joke.'
    ),
)

factory_agent = Agent('gemini-1.5-pro', result_type=list[str])

@joke_agent.tool
async def joke_factory(ctx: RunContext[MyDeps], count: int) -> str:
    r = await ctx.deps.factory_agent.run(f'Please generate {count} jokes.')
    return '\n'.join(r.data)

result = joke_agent.run_sync('Tell me a joke.', deps=MyDeps(factory_agent))
print(result.data)
#> Did you hear about the toothpaste scandal? They called it Colgate.
```

## Examples

The following examples demonstrate how to use dependencies in PydanticAI:

- [Weather Agent](https://ai.pydantic.dev/examples/weather-agent/)
- [SQL Generation](https://ai.pydantic.dev/examples/sql-gen/)
- [RAG](https://ai.pydantic.dev/examples/rag/)

# function tools
Version Notice

This documentation is ahead of the last release by **10** commits. You may see documentation for features not yet supported in the latest release [v0.0.14 2024-12-19](https://github.com/pydantic/pydantic-ai/releases/tag/v0.0.14).

Function tools provide a mechanism for models to retrieve extra information to help them generate a response.

They're useful when it is impractical or impossible to put all the context an agent might need into the system prompt, or when you want to make agents' behavior more deterministic or reliable by deferring some of the logic required to generate a response to another (not necessarily AI-powered) tool.

Function tools vs. RAG

Function tools are basically the "R" of RAG (Retrieval-Augmented Generation) — they augment what the model can do by letting it request extra information.

The main semantic difference between PydanticAI Tools and RAG is RAG is synonymous with vector search, while PydanticAI tools are more general-purpose. (Note: we may add support for vector search functionality in the future, particularly an API for generating embeddings. See [#58](https://github.com/pydantic/pydantic-ai/issues/58))

There are a number of ways to register tools with an agent:

- via the [`@agent.tool`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.tool) decorator — for tools that need access to the agent [context](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.RunContext)
- via the [`@agent.tool_plain`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.tool_plain) decorator — for tools that do not need access to the agent [context](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.RunContext)
- via the [`tools`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.__init__) keyword argument to `Agent` which can take either plain functions, or instances of [`Tool`](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.Tool)

`@agent.tool` is considered the default decorator since in the majority of cases tools will need access to the agent context.

Here's an example using both:

dice\_game.py

```python
import random

from pydantic_ai import Agent, RunContext

agent = Agent(
    'gemini-1.5-flash',  
    deps_type=str,  
    system_prompt=(
        "You're a dice game, you should roll the die and see if the number "
        "you get back matches the user's guess. If so, tell them they're a winner. "
        "Use the player's name in the response."
    ),
)

@agent.tool_plain  
def roll_die() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))

@agent.tool  
def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps

dice_result = agent.run_sync('My guess is 4', deps='Anne')  
print(dice_result.data)
#> Congratulations Anne, you guessed correctly! You're a winner!
```

*(This example is complete, it can be run "as is")*

Let's print the messages from that game to see what happened:

dice\_game\_messages.py

```python
from dice_game import dice_result

print(dice_result.all_messages())
"""
[
    ModelRequest(
        parts=[
            SystemPromptPart(
                content="You're a dice game, you should roll the die and see if the number you get back matches the user's guess. If so, tell them they're a winner. Use the player's name in the response.",
                part_kind='system-prompt',
            ),
            UserPromptPart(
                content='My guess is 4',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            ),
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='roll_die',
                args=ArgsDict(args_dict={}),
                tool_call_id=None,
                part_kind='tool-call',
            )
        ],
        timestamp=datetime.datetime(...),
        kind='response',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='roll_die',
                content='4',
                tool_call_id=None,
                timestamp=datetime.datetime(...),
                part_kind='tool-return',
            )
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='get_player_name',
                args=ArgsDict(args_dict={}),
                tool_call_id=None,
                part_kind='tool-call',
            )
        ],
        timestamp=datetime.datetime(...),
        kind='response',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='get_player_name',
                content='Anne',
                tool_call_id=None,
                timestamp=datetime.datetime(...),
                part_kind='tool-return',
            )
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content="Congratulations Anne, you guessed correctly! You're a winner!",
                part_kind='text',
            )
        ],
        timestamp=datetime.datetime(...),
        kind='response',
    ),
]
"""
```

We can represent this with a diagram:

As well as using the decorators, we can register tools via the `tools` argument to the [`Agent` constructor](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.__init__). This is useful when you want to re-use tools, and can also give more fine-grained control over the tools.

dice\_game\_tool\_kwarg.py

```python
import random

from pydantic_ai import Agent, RunContext, Tool

def roll_die() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))

def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps

agent_a = Agent(
    'gemini-1.5-flash',
    deps_type=str,
    tools=[roll_die, get_player_name],  
)
agent_b = Agent(
    'gemini-1.5-flash',
    deps_type=str,
    tools=[  
        Tool(roll_die, takes_ctx=False),
        Tool(get_player_name, takes_ctx=True),
    ],
)
dice_result = agent_b.run_sync('My guess is 4', deps='Anne')
print(dice_result.data)
#> Congratulations Anne, you guessed correctly! You're a winner!
```

*(This example is complete, it can be run "as is")*

As the name suggests, function tools use the model's "tools" or "functions" API to let the model know what is available to call. Tools or functions are also used to define the schema(s) for structured responses, thus a model might have access to many tools, some of which call function tools while others end the run and return a result.

Function parameters are extracted from the function signature, and all parameters except `RunContext` are used to build the schema for that tool call.

Even better, PydanticAI extracts the docstring from functions and (thanks to [griffe](https://mkdocstrings.github.io/griffe/)) extracts parameter descriptions from the docstring and adds them to the schema.

[Griffe supports](https://mkdocstrings.github.io/griffe/reference/docstrings/#docstrings) extracting parameter descriptions from `google`, `numpy` and `sphinx` style docstrings, and PydanticAI will infer the format to use based on the docstring. We plan to add support in the future to explicitly set the style to use, and warn/error if not all parameters are documented; see [#59](https://github.com/pydantic/pydantic-ai/issues/59).

To demonstrate a tool's schema, here we use [`FunctionModel`](https://ai.pydantic.dev/api/models/function/#pydantic_ai.models.function.FunctionModel) to print the schema a model would receive:

tool\_schema.py

```python
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models.function import AgentInfo, FunctionModel

agent = Agent()

@agent.tool_plain
def foobar(a: int, b: str, c: dict[str, list[float]]) -> str:
    """Get me foobar.

    Args:
        a: apple pie
        b: banana cake
        c: carrot smoothie
    """
    return f'{a} {b} {c}'

def print_schema(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    tool = info.function_tools[0]
    print(tool.description)
    #> Get me foobar.
    print(tool.parameters_json_schema)
    """
    {
        'properties': {
            'a': {'description': 'apple pie', 'title': 'A', 'type': 'integer'},
            'b': {'description': 'banana cake', 'title': 'B', 'type': 'string'},
            'c': {
                'additionalProperties': {'items': {'type': 'number'}, 'type': 'array'},
                'description': 'carrot smoothie',
                'title': 'C',
                'type': 'object',
            },
        },
        'required': ['a', 'b', 'c'],
        'type': 'object',
        'additionalProperties': False,
    }
    """
    return ModelResponse.from_text(content='foobar')

agent.run_sync('hello', model=FunctionModel(print_schema))
```

*(This example is complete, it can be run "as is")*

The return type of tool can be anything which Pydantic can serialize to JSON as some models (e.g. Gemini) support semi-structured return values, some expect text (OpenAI) but seem to be just as good at extracting meaning from the data. If a Python object is returned and the model expects a string, the value will be serialized to JSON.

If a tool has a single parameter that can be represented as an object in JSON schema (e.g. dataclass, TypedDict, pydantic model), the schema for the tool is simplified to be just that object.

Here's an example, we use [`TestModel.agent_model_function_tools`](https://ai.pydantic.dev/api/models/test/#pydantic_ai.models.test.TestModel.agent_model_function_tools) to inspect the tool schema that would be passed to the model.

single\_parameter\_tool.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

agent = Agent()

class Foobar(BaseModel):
    """This is a Foobar"""

    x: int
    y: str
    z: float = 3.14

@agent.tool_plain
def foobar(f: Foobar) -> str:
    return str(f)

test_model = TestModel()
result = agent.run_sync('hello', model=test_model)
print(result.data)
#> {"foobar":"x=0 y='a' z=3.14"}
print(test_model.agent_model_function_tools)
"""
[
    ToolDefinition(
        name='foobar',
        description='This is a Foobar',
        parameters_json_schema={
            'properties': {
                'x': {'title': 'X', 'type': 'integer'},
                'y': {'title': 'Y', 'type': 'string'},
                'z': {'default': 3.14, 'title': 'Z', 'type': 'number'},
            },
            'required': ['x', 'y'],
            'title': 'Foobar',
            'type': 'object',
        },
        outer_typed_dict_key=None,
    )
]
"""
```

*(This example is complete, it can be run "as is")*

Tools can optionally be defined with another function: `prepare`, which is called at each step of a run to customize the definition of the tool passed to the model, or omit the tool completely from that step.

A `prepare` method can be registered via the `prepare` kwarg to any of the tool registration mechanisms:

- [`@agent.tool`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.tool) decorator
- [`@agent.tool_plain`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.tool_plain) decorator
- [`Tool`](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.Tool) dataclass

The `prepare` method, should be of type [`ToolPrepareFunc`](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.ToolPrepareFunc), a function which takes [`RunContext`](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.RunContext) and a pre-built [`ToolDefinition`](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.ToolDefinition), and should either return that `ToolDefinition` with or without modifying it, return a new `ToolDefinition`, or return `None` to indicate this tools should not be registered for that step.

Here's a simple `prepare` method that only includes the tool if the value of the dependency is `42`.

As with the previous example, we use [`TestModel`](https://ai.pydantic.dev/api/models/test/#pydantic_ai.models.test.TestModel) to demonstrate the behavior without calling a real model.

tool\_only\_if\_42.py

```python
from typing import Union

from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import ToolDefinition

agent = Agent('test')

async def only_if_42(
    ctx: RunContext[int], tool_def: ToolDefinition
) -> Union[ToolDefinition, None]:
    if ctx.deps == 42:
        return tool_def

@agent.tool(prepare=only_if_42)
def hitchhiker(ctx: RunContext[int], answer: str) -> str:
    return f'{ctx.deps} {answer}'

result = agent.run_sync('testing...', deps=41)
print(result.data)
#> success (no tool calls)
result = agent.run_sync('testing...', deps=42)
print(result.data)
#> {"hitchhiker":"42 a"}
```

*(This example is complete, it can be run "as is")*

Here's a more complex example where we change the description of the `name` parameter to based on the value of `deps`

For the sake of variation, we create this tool using the [`Tool`](https://ai.pydantic.dev/api/tools/#pydantic_ai.tools.Tool) dataclass.

customize\_name.py

```python
from __future__ import annotations

from typing import Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel
from pydantic_ai.tools import Tool, ToolDefinition

def greet(name: str) -> str:
    return f'hello {name}'

async def prepare_greet(
    ctx: RunContext[Literal['human', 'machine']], tool_def: ToolDefinition
) -> ToolDefinition | None:
    d = f'Name of the {ctx.deps} to greet.'
    tool_def.parameters_json_schema['properties']['name']['description'] = d
    return tool_def

greet_tool = Tool(greet, prepare=prepare_greet)
test_model = TestModel()
agent = Agent(test_model, tools=[greet_tool], deps_type=Literal['human', 'machine'])

result = agent.run_sync('testing...', deps='human')
print(result.data)
#> {"greet":"hello a"}
print(test_model.agent_model_function_tools)
"""
[
    ToolDefinition(
        name='greet',
        description='',
        parameters_json_schema={
            'properties': {
                'name': {
                    'title': 'Name',
                    'type': 'string',
                    'description': 'Name of the human to greet.',
                }
            },
            'required': ['name'],
            'type': 'object',
            'additionalProperties': False,
        },
        outer_typed_dict_key=None,
    )
]
"""
```

*(This example is complete, it can be run "as is")*

# messages and chat history
Version Notice

This documentation is ahead of the last release by **10** commits. You may see documentation for features not yet supported in the latest release [v0.0.14 2024-12-19](https://github.com/pydantic/pydantic-ai/releases/tag/v0.0.14).

PydanticAI provides access to messages exchanged during an agent run. These messages can be used both to continue a coherent conversation, and to understand how an agent performed.

### Accessing Messages from Results

After running an agent, you can access the messages exchanged during that run from the `result` object.

Both [`RunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult) (returned by [`Agent.run`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run), [`Agent.run_sync`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run_sync)) and [`StreamedRunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.StreamedRunResult) (returned by [`Agent.run_stream`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run_stream)) have the following methods:

- [`all_messages()`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult.all_messages): returns all messages, including messages from prior runs. There's also a variant that returns JSON bytes, [`all_messages_json()`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult.all_messages_json).
- [`new_messages()`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult.new_messages): returns only the messages from the current run. There's also a variant that returns JSON bytes, [`new_messages_json()`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult.new_messages_json).

Example of accessing methods on a [`RunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult) :

run\_result\_messages.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

result = agent.run_sync('Tell me a joke.')
print(result.data)
#> Did you hear about the toothpaste scandal? They called it Colgate.

# all messages from the run
print(result.all_messages())
"""
[
    ModelRequest(
        parts=[
            SystemPromptPart(
                content='Be a helpful assistant.', part_kind='system-prompt'
            ),
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            ),
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.',
                part_kind='text',
            )
        ],
        timestamp=datetime.datetime(...),
        kind='response',
    ),
]
"""
```

*(This example is complete, it can be run "as is")*

Example of accessing methods on a [`StreamedRunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.StreamedRunResult) :

streamed\_run\_result\_messages.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

async def main():
    async with agent.run_stream('Tell me a joke.') as result:
        # incomplete messages before the stream finishes
        print(result.all_messages())
        """
        [
            ModelRequest(
                parts=[
                    SystemPromptPart(
                        content='Be a helpful assistant.', part_kind='system-prompt'
                    ),
                    UserPromptPart(
                        content='Tell me a joke.',
                        timestamp=datetime.datetime(...),
                        part_kind='user-prompt',
                    ),
                ],
                kind='request',
            )
        ]
        """

        async for text in result.stream():
            print(text)
            #> Did you hear
            #> Did you hear about the toothpaste
            #> Did you hear about the toothpaste scandal? They called
            #> Did you hear about the toothpaste scandal? They called it Colgate.

        # complete messages once the stream finishes
        print(result.all_messages())
        """
        [
            ModelRequest(
                parts=[
                    SystemPromptPart(
                        content='Be a helpful assistant.', part_kind='system-prompt'
                    ),
                    UserPromptPart(
                        content='Tell me a joke.',
                        timestamp=datetime.datetime(...),
                        part_kind='user-prompt',
                    ),
                ],
                kind='request',
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='Did you hear about the toothpaste scandal? They called it Colgate.',
                        part_kind='text',
                    )
                ],
                timestamp=datetime.datetime(...),
                kind='response',
            ),
        ]
        """
```

*(This example is complete, it can be run "as is")*

### Using Messages as Input for Further Agent Runs

The primary use of message histories in PydanticAI is to maintain context across multiple agent runs.

To use existing messages in a run, pass them to the `message_history` parameter of [`Agent.run`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run), [`Agent.run_sync`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run_sync) or [`Agent.run_stream`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run_stream).

If `message_history` is set and not empty, a new system prompt is not generated — we assume the existing message history includes a system prompt.

Reusing messages in a conversation

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.data)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync('Explain?', message_history=result1.new_messages())
print(result2.data)
#> This is an excellent joke invent by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            SystemPromptPart(
                content='Be a helpful assistant.', part_kind='system-prompt'
            ),
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            ),
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.',
                part_kind='text',
            )
        ],
        timestamp=datetime.datetime(...),
        kind='response',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            )
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invent by Samuel Colvin, it needs no explanation.',
                part_kind='text',
            )
        ],
        timestamp=datetime.datetime(...),
        kind='response',
    ),
]
"""
```

*(This example is complete, it can be run "as is")*

## Other ways of using messages

Since messages are defined by simple dataclasses, you can manually create and manipulate, e.g. for testing.

The message format is independent of the model used, so you can use messages in different agents, or the same agent with different models.

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.data)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync(
    'Explain?', model='gemini-1.5-pro', message_history=result1.new_messages()
)
print(result2.data)
#> This is an excellent joke invent by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            SystemPromptPart(
                content='Be a helpful assistant.', part_kind='system-prompt'
            ),
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            ),
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.',
                part_kind='text',
            )
        ],
        timestamp=datetime.datetime(...),
        kind='response',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            )
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invent by Samuel Colvin, it needs no explanation.',
                part_kind='text',
            )
        ],
        timestamp=datetime.datetime(...),
        kind='response',
    ),
]
"""
```

## Examples

For a more complete example of using messages in conversations, see the [chat app](https://ai.pydantic.dev/examples/chat-app/) example.

# models
Version Notice

This documentation is ahead of the last release by **10** commits. You may see documentation for features not yet supported in the latest release [v0.0.14 2024-12-19](https://github.com/pydantic/pydantic-ai/releases/tag/v0.0.14).

PydanticAI is Model-agnostic and has built in support for the following model providers:

- [OpenAI](https://ai.pydantic.dev/models/#openai)
- [Anthropic](https://ai.pydantic.dev/models/#anthropic)
- Gemini via two different APIs: [Generative Language API](https://ai.pydantic.dev/models/#gemini) and [VertexAI API](https://ai.pydantic.dev/models/#gemini-via-vertexai)
- [Ollama](https://ai.pydantic.dev/models/#ollama)
- [Groq](https://ai.pydantic.dev/models/#groq)
- [Mistral](https://ai.pydantic.dev/models/#mistral)

You can also [add support for other models](https://ai.pydantic.dev/models/#implementing-custom-models).

PydanticAI also comes with [`TestModel`](https://ai.pydantic.dev/api/models/test/) and [`FunctionModel`](https://ai.pydantic.dev/api/models/function/) for testing and development.

To use each model provider, you need to configure your local environment and make sure you have the right packages installed.

## OpenAI

### Install

To use OpenAI models, you need to either install [`pydantic-ai`](https://ai.pydantic.dev/install/), or install [`pydantic-ai-slim`](https://ai.pydantic.dev/install/#slim-install) with the `openai` optional group:

```
pip install 'pydantic-ai-slim[openai]'
```

```
uv add 'pydantic-ai-slim[openai]'
```

### Configuration

To use [`OpenAIModel`](https://ai.pydantic.dev/api/models/openai/#pydantic_ai.models.openai.OpenAIModel) through their main API, go to [platform.openai.com](https://platform.openai.com/) and follow your nose until you find the place to generate an API key.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export OPENAI_API_KEY='your-api-key'
```

You can then use [`OpenAIModel`](https://ai.pydantic.dev/api/models/openai/#pydantic_ai.models.openai.OpenAIModel) by name:

openai\_model\_by\_name.py

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')
...
```

Or initialise the model directly with just the model name:

openai\_model\_init.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

model = OpenAIModel('gpt-4o')
agent = Agent(model)
...
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the [`api_key` argument](https://ai.pydantic.dev/api/models/openai/#pydantic_ai.models.openai.OpenAIModel.__init__):

openai\_model\_api\_key.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

model = OpenAIModel('gpt-4o', api_key='your-api-key')
agent = Agent(model)
...
```

### `base_url` argument

To use another OpenAI-compatible API, such as [OpenRouter](https://openrouter.ai/), you can make use of the [`base_url` argument](https://ai.pydantic.dev/api/models/openai/#pydantic_ai.models.openai.OpenAIModel.__init__):

openai\_model\_base\_url.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

model = OpenAIModel(
    'anthropic/claude-3.5-sonnet',
    base_url='https://openrouter.ai/api/v1',
    api_key='your-api-key',
)
agent = Agent(model)
...
```

### Custom OpenAI Client

`OpenAIModel` also accepts a custom `AsyncOpenAI` client via the [`openai_client` parameter](https://ai.pydantic.dev/api/models/openai/#pydantic_ai.models.openai.OpenAIModel.__init__), so you can customise the `organization`, `project`, `base_url` etc. as defined in the [OpenAI API docs](https://platform.openai.com/docs/api-reference).

You could also use the [`AsyncAzureOpenAI`](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/switching-endpoints) client to use the Azure OpenAI API.

openai\_azure.py

```python
from openai import AsyncAzureOpenAI

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

client = AsyncAzureOpenAI(
    azure_endpoint='...',
    api_version='2024-07-01-preview',
    api_key='your-api-key',
)

model = OpenAIModel('gpt-4o', openai_client=client)
agent = Agent(model)
...
```

## Anthropic

### Install

To use [`AnthropicModel`](https://ai.pydantic.dev/api/models/anthropic/#pydantic_ai.models.anthropic.AnthropicModel) models, you need to either install [`pydantic-ai`](https://ai.pydantic.dev/install/), or install [`pydantic-ai-slim`](https://ai.pydantic.dev/install/#slim-install) with the `anthropic` optional group:

```
pip install 'pydantic-ai-slim[anthropic]'
```

```
uv add 'pydantic-ai-slim[anthropic]'
```

### Configuration

To use [Anthropic](https://anthropic.com/) through their API, go to [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) to generate an API key.

[`AnthropicModelName`](https://ai.pydantic.dev/api/models/anthropic/#pydantic_ai.models.anthropic.AnthropicModelName) contains a list of available Anthropic models.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export ANTHROPIC_API_KEY='your-api-key'
```

You can then use [`AnthropicModel`](https://ai.pydantic.dev/api/models/anthropic/#pydantic_ai.models.anthropic.AnthropicModel) by name:

anthropic\_model\_by\_name.py

```py
from pydantic_ai import Agent

agent = Agent('claude-3-5-sonnet-latest')
...
```

Or initialise the model directly with just the model name:

anthropic\_model\_init.py

```py
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-3-5-sonnet-latest')
agent = Agent(model)
...
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the [`api_key` argument](https://ai.pydantic.dev/api/models/anthropic/#pydantic_ai.models.anthropic.AnthropicModel.__init__):

anthropic\_model\_api\_key.py

```py
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-3-5-sonnet-latest', api_key='your-api-key')
agent = Agent(model)
...
```

## Gemini

For prototyping only

Google themselves refer to this API as the "hobby" API, I've received 503 responses from it a number of times. The API is easy to use and useful for prototyping and simple demos, but I would not rely on it in production.

If you want to run Gemini models in production, you should use the [VertexAI API](https://ai.pydantic.dev/models/#gemini-via-vertexai) described below.

### Install

To use [`GeminiModel`](https://ai.pydantic.dev/api/models/gemini/#pydantic_ai.models.gemini.GeminiModel) models, you just need to install [`pydantic-ai`](https://ai.pydantic.dev/install/) or [`pydantic-ai-slim`](https://ai.pydantic.dev/install/#slim-install), no extra dependencies are required.

### Configuration

[`GeminiModel`](https://ai.pydantic.dev/api/models/gemini/#pydantic_ai.models.gemini.GeminiModel) let's you use the Google's Gemini models through their [Generative Language API](https://ai.google.dev/api/all-methods), `generativelanguage.googleapis.com`.

[`GeminiModelName`](https://ai.pydantic.dev/api/models/gemini/#pydantic_ai.models.gemini.GeminiModelName) contains a list of available Gemini models that can be used through this interface.

To use `GeminiModel`, go to [aistudio.google.com](https://aistudio.google.com/) and follow your nose until you find the place to generate an API key.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export GEMINI_API_KEY=your-api-key
```

You can then use [`GeminiModel`](https://ai.pydantic.dev/api/models/gemini/#pydantic_ai.models.gemini.GeminiModel) by name:

gemini\_model\_by\_name.py

```python
from pydantic_ai import Agent

agent = Agent('gemini-1.5-flash')
...
```

Or initialise the model directly with just the model name:

gemini\_model\_init.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel

model = GeminiModel('gemini-1.5-flash')
agent = Agent(model)
...
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the [`api_key` argument](https://ai.pydantic.dev/api/models/gemini/#pydantic_ai.models.gemini.GeminiModel.__init__):

gemini\_model\_api\_key.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel

model = GeminiModel('gemini-1.5-flash', api_key='your-api-key')
agent = Agent(model)
...
```

## Gemini via VertexAI

To run Google's Gemini models in production, you should use [`VertexAIModel`](https://ai.pydantic.dev/api/models/vertexai/#pydantic_ai.models.vertexai.VertexAIModel) which uses the `*-aiplatform.googleapis.com` API.

[`GeminiModelName`](https://ai.pydantic.dev/api/models/gemini/#pydantic_ai.models.gemini.GeminiModelName) contains a list of available Gemini models that can be used through this interface.

### Install

To use [`VertexAIModel`](https://ai.pydantic.dev/api/models/vertexai/#pydantic_ai.models.vertexai.VertexAIModel), you need to either install [`pydantic-ai`](https://ai.pydantic.dev/install/), or install [`pydantic-ai-slim`](https://ai.pydantic.dev/install/#slim-install) with the `vertexai` optional group:

```
pip install 'pydantic-ai-slim[vertexai]'
```

```
uv add 'pydantic-ai-slim[vertexai]'
```

### Configuration

This interface has a number of advantages over `generativelanguage.googleapis.com` documented above:

1. The VertexAI API is more reliably and marginally lower latency in our experience.
2. You can [purchase provisioned throughput](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput#purchase-provisioned-throughput) with VertexAI to guarantee capacity.
3. If you're running PydanticAI inside GCP, you don't need to set up authentication, it should "just work".
4. You can decide which region to use, which might be important from a regulatory perspective, and might improve latency.

The big disadvantage is that for local development you may need to create and configure a "service account", which I've found extremely painful to get right in the past.

Whichever way you authenticate, you'll need to have VertexAI enabled in your GCP account.

### Application default credentials

Luckily if you're running PydanticAI inside GCP, or you have the [`gcloud` CLI](https://cloud.google.com/sdk/gcloud) installed and configured, you should be able to use `VertexAIModel` without any additional setup.

To use `VertexAIModel`, with [application default credentials](https://cloud.google.com/docs/authentication/application-default-credentials) configured (e.g. with `gcloud`), you can simply use:

vertexai\_application\_default\_credentials.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.vertexai import VertexAIModel

model = VertexAIModel('gemini-1.5-flash')
agent = Agent(model)
...
```

Internally this uses [`google.auth.default()`](https://google-auth.readthedocs.io/en/master/reference/google.auth.html) from the `google-auth` package to obtain credentials.

Won't fail until `agent.run()`

Because `google.auth.default()` requires network requests and can be slow, it's not run until you call `agent.run()`. Meaning any configuration or permissions error will only be raised when you try to use the model. To for this check to be run, call [`await model.ainit()`](https://ai.pydantic.dev/api/models/vertexai/#pydantic_ai.models.vertexai.VertexAIModel.ainit).

You may also need to pass the [`project_id` argument to `VertexAIModel`](https://ai.pydantic.dev/api/models/vertexai/#pydantic_ai.models.vertexai.VertexAIModel.__init__) if application default credentials don't set a project, if you pass `project_id` and it conflicts with the project set by application default credentials, an error is raised.

### Service account

If instead of application default credentials, you want to authenticate with a service account, you'll need to create a service account, add it to your GCP project (note: AFAIK this step is necessary even if you created the service account within the project), give that service account the "Vertex AI Service Agent" role, and download the service account JSON file.

Once you have the JSON file, you can use it thus:

vertexai\_service\_account.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.vertexai import VertexAIModel

model = VertexAIModel(
    'gemini-1.5-flash',
    service_account_file='path/to/service-account.json',
)
agent = Agent(model)
...
```

### Customising region

Whichever way you authenticate, you can specify which region requests will be sent to via the [`region` argument](https://ai.pydantic.dev/api/models/vertexai/#pydantic_ai.models.vertexai.VertexAIModel.__init__).

Using a region close to your application can improve latency and might be important from a regulatory perspective.

vertexai\_region.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.vertexai import VertexAIModel

model = VertexAIModel('gemini-1.5-flash', region='asia-east1')
agent = Agent(model)
...
```

[`VertexAiRegion`](https://ai.pydantic.dev/api/models/vertexai/#pydantic_ai.models.vertexai.VertexAiRegion) contains a list of available regions.

## Ollama

### Install

To use [`OllamaModel`](https://ai.pydantic.dev/api/models/ollama/#pydantic_ai.models.ollama.OllamaModel), you need to either install [`pydantic-ai`](https://ai.pydantic.dev/install/), or install [`pydantic-ai-slim`](https://ai.pydantic.dev/install/#slim-install) with the `openai` optional group:

```
pip install 'pydantic-ai-slim[openai]'
```

```
uv add 'pydantic-ai-slim[openai]'
```

**This is because internally, `OllamaModel` uses the OpenAI API.**

### Configuration

To use [Ollama](https://ollama.com/), you must first download the Ollama client, and then download a model using the [Ollama model library](https://ollama.com/library).

You must also ensure the Ollama server is running when trying to make requests to it. For more information, please see the [Ollama documentation](https://github.com/ollama/ollama/tree/main/docs).

For detailed setup and example, please see the [Ollama setup documentation](https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/ollama.md).

## Groq

### Install

To use [`GroqModel`](https://ai.pydantic.dev/api/models/groq/#pydantic_ai.models.groq.GroqModel), you need to either install [`pydantic-ai`](https://ai.pydantic.dev/install/), or install [`pydantic-ai-slim`](https://ai.pydantic.dev/install/#slim-install) with the `groq` optional group:

```
pip install 'pydantic-ai-slim[groq]'
```

```
uv add 'pydantic-ai-slim[groq]'
```

### Configuration

To use [Groq](https://groq.com/) through their API, go to [console.groq.com/keys](https://console.groq.com/keys) and follow your nose until you find the place to generate an API key.

[`GroqModelName`](https://ai.pydantic.dev/api/models/groq/#pydantic_ai.models.groq.GroqModelName) contains a list of available Groq models.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export GROQ_API_KEY='your-api-key'
```

You can then use [`GroqModel`](https://ai.pydantic.dev/api/models/groq/#pydantic_ai.models.groq.GroqModel) by name:

groq\_model\_by\_name.py

```python
from pydantic_ai import Agent

agent = Agent('groq:llama-3.1-70b-versatile')
...
```

Or initialise the model directly with just the model name:

groq\_model\_init.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

model = GroqModel('llama-3.1-70b-versatile')
agent = Agent(model)
...
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the [`api_key` argument](https://ai.pydantic.dev/api/models/groq/#pydantic_ai.models.groq.GroqModel.__init__):

groq\_model\_api\_key.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

model = GroqModel('llama-3.1-70b-versatile', api_key='your-api-key')
agent = Agent(model)
...
```

## Mistral

### Install

To use [`MistralModel`](https://ai.pydantic.dev/api/models/mistral/#pydantic_ai.models.mistral.MistralModel), you need to either install [`pydantic-ai`](https://ai.pydantic.dev/install/), or install [`pydantic-ai-slim`](https://ai.pydantic.dev/install/#slim-install) with the `mistral` optional group:

```
pip install 'pydantic-ai-slim[mistral]'
```

```
uv add 'pydantic-ai-slim[mistral]'
```

### Configuration

To use [Mistral](https://mistral.ai/) through their API, go to [console.mistral.ai/api-keys/](https://console.mistral.ai/api-keys/) and follow your nose until you find the place to generate an API key.

[`NamedMistralModels`](https://ai.pydantic.dev/api/models/mistral/#pydantic_ai.models.mistral.NamedMistralModels) contains a list of the most popular Mistral models.

### Environment variable

Once you have the API key, you can set it as an environment variable:

```bash
export MISTRAL_API_KEY='your-api-key'
```

You can then use [`MistralModel`](https://ai.pydantic.dev/api/models/mistral/#pydantic_ai.models.mistral.MistralModel) by name:

mistral\_model\_by\_name.py

```python
from pydantic_ai import Agent

agent = Agent('mistral:mistral-large-latest')
...
```

Or initialise the model directly with just the model name:

mistral\_model\_init.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel

model = MistralModel('mistral-small-latest')
agent = Agent(model)
...
```

### `api_key` argument

If you don't want to or can't set the environment variable, you can pass it at runtime via the [`api_key` argument](https://ai.pydantic.dev/api/models/mistral/#pydantic_ai.models.mistral.MistralModel.__init__):

mistral\_model\_api\_key.py

```python
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel

model = MistralModel('mistral-small-latest', api_key='your-api-key')
agent = Agent(model)
...
```

## Implementing Custom Models

To implement support for models not already supported, you will need to subclass the [`Model`](https://ai.pydantic.dev/api/models/base/#pydantic_ai.models.Model) abstract base class.

This in turn will require you to implement the following other abstract base classes:

- [`AgentModel`](https://ai.pydantic.dev/api/models/base/#pydantic_ai.models.AgentModel)
- [`StreamTextResponse`](https://ai.pydantic.dev/api/models/base/#pydantic_ai.models.StreamTextResponse)
- [`StreamStructuredResponse`](https://ai.pydantic.dev/api/models/base/#pydantic_ai.models.StreamStructuredResponse)

The best place to start is to review the source code for existing implementations, e.g. [`OpenAIModel`](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_ai_slim/pydantic_ai/models/openai.py).

For details on when we'll accept contributions adding new models to PydanticAI, see the [contributing guidelines](https://ai.pydantic.dev/contributing/#new-model-rules).

# results
Version Notice

This documentation is ahead of the last release by **10** commits. You may see documentation for features not yet supported in the latest release [v0.0.14 2024-12-19](https://github.com/pydantic/pydantic-ai/releases/tag/v0.0.14).

Results are the final values returned from [running an agent](https://ai.pydantic.dev/agents/#running-agents). The result values are wrapped in [`RunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.RunResult) and [`StreamedRunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.StreamedRunResult) so you can access other data like [usage](https://ai.pydantic.dev/api/result/#pydantic_ai.result.Usage) of the run and [message history](https://ai.pydantic.dev/message-history/#accessing-messages-from-results)

Both `RunResult` and `StreamedRunResult` are generic in the data they wrap, so typing information about the data returned by the agent is preserved.

olympics.py

```python
from pydantic import BaseModel

from pydantic_ai import Agent

class CityLocation(BaseModel):
    city: str
    country: str

agent = Agent('gemini-1.5-flash', result_type=CityLocation)
result = agent.run_sync('Where were the olympics held in 2012?')
print(result.data)
#> city='London' country='United Kingdom'
print(result.usage())
"""
Usage(requests=1, request_tokens=57, response_tokens=8, total_tokens=65, details=None)
"""
```

*(This example is complete, it can be run "as is")*

Runs end when either a plain text response is received or the model calls a tool associated with one of the structured result types. We will add limits to make sure a run doesn't go on indefinitely, see [#70](https://github.com/pydantic/pydantic-ai/issues/70).

## Result data

When the result type is `str`, or a union including `str`, plain text responses are enabled on the model, and the raw text response from the model is used as the response data.

If the result type is a union with multiple members (after remove `str` from the members), each member is registered as a separate tool with the model in order to reduce the complexity of the tool schemas and maximise the changes a model will respond correctly.

If the result type schema is not of type `"object"`, the result type is wrapped in a single element object, so the schema of all tools registered with the model are object schemas.

Structured results (like tools) use Pydantic to build the JSON schema used for the tool, and to validate the data returned by the model.

Bring on PEP-747

Until [PEP-747](https://peps.python.org/pep-0747/) "Annotating Type Forms" lands, unions are not valid as `type`s in Python.

When creating the agent we need to `# type: ignore` the `result_type` argument, and add a type hint to tell type checkers about the type of the agent.

Here's an example of returning either text or a structured value

box\_or\_error.py

```python
from typing import Union

from pydantic import BaseModel

from pydantic_ai import Agent

class Box(BaseModel):
    width: int
    height: int
    depth: int
    units: str

agent: Agent[None, Union[Box, str]] = Agent(
    'openai:gpt-4o-mini',
    result_type=Union[Box, str],  # type: ignore
    system_prompt=(
        "Extract me the dimensions of a box, "
        "if you can't extract all data, ask the user to try again."
    ),
)

result = agent.run_sync('The box is 10x20x30')
print(result.data)
#> Please provide the units for the dimensions (e.g., cm, in, m).

result = agent.run_sync('The box is 10x20x30 cm')
print(result.data)
#> width=10 height=20 depth=30 units='cm'
```

*(This example is complete, it can be run "as is")*

Here's an example of using a union return type which registered multiple tools, and wraps non-object schemas in an object:

colors\_or\_sizes.py

```python
from typing import Union

from pydantic_ai import Agent

agent: Agent[None, Union[list[str], list[int]]] = Agent(
    'openai:gpt-4o-mini',
    result_type=Union[list[str], list[int]],  # type: ignore
    system_prompt='Extract either colors or sizes from the shapes provided.',
)

result = agent.run_sync('red square, blue circle, green triangle')
print(result.data)
#> ['red', 'blue', 'green']

result = agent.run_sync('square size 10, circle size 20, triangle size 30')
print(result.data)
#> [10, 20, 30]
```

*(This example is complete, it can be run "as is")*

### Result validators functions

Some validation is inconvenient or impossible to do in Pydantic validators, in particular when the validation requires IO and is asynchronous. PydanticAI provides a way to add validation functions via the [`agent.result_validator`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.result_validator) decorator.

Here's a simplified variant of the [SQL Generation example](https://ai.pydantic.dev/examples/sql-gen/):

sql\_gen.py

```python
from typing import Union

from fake_database import DatabaseConn, QueryError
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry

class Success(BaseModel):
    sql_query: str

class InvalidRequest(BaseModel):
    error_message: str

Response = Union[Success, InvalidRequest]
agent: Agent[DatabaseConn, Response] = Agent(
    'gemini-1.5-flash',
    result_type=Response,  # type: ignore
    deps_type=DatabaseConn,
    system_prompt='Generate PostgreSQL flavored SQL queries based on user input.',
)

@agent.result_validator
async def validate_result(ctx: RunContext[DatabaseConn], result: Response) -> Response:
    if isinstance(result, InvalidRequest):
        return result
    try:
        await ctx.deps.execute(f'EXPLAIN {result.sql_query}')
    except QueryError as e:
        raise ModelRetry(f'Invalid query: {e}') from e
    else:
        return result

result = agent.run_sync(
    'get me uses who were last active yesterday.', deps=DatabaseConn()
)
print(result.data)
#> sql_query='SELECT * FROM users WHERE last_active::date = today() - interval 1 day'
```

*(This example is complete, it can be run "as is")*

## Streamed Results

There two main challenges with streamed results:

1. Validating structured responses before they're complete, this is achieved by "partial validation" which was recently added to Pydantic in [pydantic/pydantic#10748](https://github.com/pydantic/pydantic/pull/10748).
2. When receiving a response, we don't know if it's the final response without starting to stream it and peeking at the content. PydanticAI streams just enough of the response to sniff out if it's a tool call or a result, then streams the whole thing and calls tools, or returns the stream as a [`StreamedRunResult`](https://ai.pydantic.dev/api/result/#pydantic_ai.result.StreamedRunResult).

### Streaming Text

Example of streamed text result:

streamed\_hello\_world.py

```python
from pydantic_ai import Agent

agent = Agent('gemini-1.5-flash')  

async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:  
        async for message in result.stream():  
            print(message)
            #> The first known
            #> The first known use of "hello,
            #> The first known use of "hello, world" was in
            #> The first known use of "hello, world" was in a 1974 textbook
            #> The first known use of "hello, world" was in a 1974 textbook about the C
            #> The first known use of "hello, world" was in a 1974 textbook about the C programming language.
```

*(This example is complete, it can be run "as is")*

We can also stream text as deltas rather than the entire text in each item:

streamed\_delta\_hello\_world.py

```python
from pydantic_ai import Agent

agent = Agent('gemini-1.5-flash')

async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        async for message in result.stream_text(delta=True):  
            print(message)
            #> The first known
            #> use of "hello,
            #> world" was in
            #> a 1974 textbook
            #> about the C
            #> programming language.
```

*(This example is complete, it can be run "as is")*

Result message not included in `messages`

The final result message will **NOT** be added to result messages if you use `.stream_text(delta=True)`, see [Messages and chat history](https://ai.pydantic.dev/message-history/) for more information.

### Streaming Structured Responses

Not all types are supported with partial validation in Pydantic, see [pydantic/pydantic#10748](https://github.com/pydantic/pydantic/pull/10748), generally for model-like structures it's currently best to use `TypeDict`.

Here's an example of streaming a use profile as it's built:

streamed\_user\_profile.py

```python
from datetime import date

from typing_extensions import TypedDict

from pydantic_ai import Agent

class UserProfile(TypedDict, total=False):
    name: str
    dob: date
    bio: str

agent = Agent(
    'openai:gpt-4o',
    result_type=UserProfile,
    system_prompt='Extract a user profile from the input',
)

async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for profile in result.stream():
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
```

*(This example is complete, it can be run "as is")*

If you want fine-grained control of validation, particularly catching validation errors, you can use the following pattern:

streamed\_user\_profile.py

```python
from datetime import date

from pydantic import ValidationError
from typing_extensions import TypedDict

from pydantic_ai import Agent

class UserProfile(TypedDict, total=False):
    name: str
    dob: date
    bio: str

agent = Agent('openai:gpt-4o', result_type=UserProfile)

async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for message, last in result.stream_structured(debounce_by=0.01):  
            try:
                profile = await result.validate_structured_result(  
                    message,
                    allow_partial=not last,
                )
            except ValidationError:
                continue
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
```

*(This example is complete, it can be run "as is")*

## Examples

The following examples demonstrate how to use streamed responses in PydanticAI:

- [Stream markdown](https://ai.pydantic.dev/examples/stream-markdown/)
- [Stream Whales](https://ai.pydantic.dev/examples/stream-whales/)
# testing and evals
Version Notice

This documentation is ahead of the last release by **10** commits. You may see documentation for features not yet supported in the latest release [v0.0.14 2024-12-19](https://github.com/pydantic/pydantic-ai/releases/tag/v0.0.14).

With PydanticAI and LLM integrations in general, there are two distinct kinds of test:

1. **Unit tests** — tests of your application code, and whether it's behaving correctly
2. **Evals** — tests of the LLM, and how good or bad its responses are

For the most part, these two kinds of tests have pretty separate goals and considerations.

## Unit tests

Unit tests for PydanticAI code are just like unit tests for any other Python code.

Because for the most part they're nothing new, we have pretty well established tools and patterns for writing and running these kinds of tests.

Unless you're really sure you know better, you'll probably want to follow roughly this strategy:

- Use [`pytest`](https://docs.pytest.org/en/stable/) as your test harness
- If you find yourself typing out long assertions, use [inline-snapshot](https://15r10nk.github.io/inline-snapshot/latest/)
- Similarly, [dirty-equals](https://dirty-equals.helpmanual.io/latest/) can be useful for comparing large data structures
- Use [`TestModel`](https://ai.pydantic.dev/api/models/test/#pydantic_ai.models.test.TestModel) or [`FunctionModel`](https://ai.pydantic.dev/api/models/function/#pydantic_ai.models.function.FunctionModel) in place of your actual model to avoid the usage, latency and variability of real LLM calls
- Use [`Agent.override`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.override) to replace your model inside your application logic
- Set [`ALLOW_MODEL_REQUESTS=False`](https://ai.pydantic.dev/api/models/base/#pydantic_ai.models.ALLOW_MODEL_REQUESTS) globally to block any requests from being made to non-test models accidentally

### Unit testing with `TestModel`

The simplest and fastest way to exercise most of your application code is using [`TestModel`](https://ai.pydantic.dev/api/models/test/#pydantic_ai.models.test.TestModel), this will (by default) call all tools in the agent, then return either plain text or a structured response depending on the return type of the agent.

`TestModel` is not magic

The "clever" (but not too clever) part of `TestModel` is that it will attempt to generate valid structured data for [function tools](https://ai.pydantic.dev/tools/) and [result types](https://ai.pydantic.dev/results/#structured-result-validation) based on the schema of the registered tools.

There's no ML or AI in `TestModel`, it's just plain old procedural Python code that tries to generate data that satisfies the JSON schema of a tool.

The resulting data won't look pretty or relevant, but it should pass Pydantic's validation in most cases. If you want something more sophisticated, use [`FunctionModel`](https://ai.pydantic.dev/api/models/function/#pydantic_ai.models.function.FunctionModel) and write your own data generation logic.

Let's write unit tests for the following application code:

weather\_app.py

```python
import asyncio
from datetime import date

from pydantic_ai import Agent, RunContext

from fake_database import DatabaseConn  
from weather_service import WeatherService  

weather_agent = Agent(
    'openai:gpt-4o',
    deps_type=WeatherService,
    system_prompt='Providing a weather forecast at the locations the user provides.',
)

@weather_agent.tool
def weather_forecast(
    ctx: RunContext[WeatherService], location: str, forecast_date: date
) -> str:
    if forecast_date < date.today():  
        return ctx.deps.get_historic_weather(location, forecast_date)
    else:
        return ctx.deps.get_forecast(location, forecast_date)

async def run_weather_forecast(  
    user_prompts: list[tuple[str, int]], conn: DatabaseConn
):
    """Run weather forecast for a list of user prompts and save."""
    async with WeatherService() as weather_service:

        async def run_forecast(prompt: str, user_id: int):
            result = await weather_agent.run(prompt, deps=weather_service)
            await conn.store_forecast(user_id, result.data)

        # run all prompts in parallel
        await asyncio.gather(
            *(run_forecast(prompt, user_id) for (prompt, user_id) in user_prompts)
        )
```

Here we have a function that takes a list of `(user_prompt, user_id)` tuples, gets a weather forecast for each prompt, and stores the result in the database.

**We want to test this code without having to mock certain objects or modify our code so we can pass test objects in.**

Here's how we would write tests using [`TestModel`](https://ai.pydantic.dev/api/models/test/#pydantic_ai.models.test.TestModel):

test\_weather\_app.py

```python
from datetime import timezone
import pytest

from dirty_equals import IsNow

from pydantic_ai import models
from pydantic_ai.models.test import TestModel
from pydantic_ai.messages import (
    ArgsDict,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    ModelRequest,
)

from fake_database import DatabaseConn
from weather_app import run_weather_forecast, weather_agent

pytestmark = pytest.mark.anyio  
models.ALLOW_MODEL_REQUESTS = False  

async def test_forecast():
    conn = DatabaseConn()
    user_id = 1
    with weather_agent.override(model=TestModel()):  
        prompt = 'What will the weather be like in London on 2024-11-28?'
        await run_weather_forecast([(prompt, user_id)], conn)  

    forecast = await conn.get_forecast(user_id)
    assert forecast == '{"weather_forecast":"Sunny with a chance of rain"}'  

    assert weather_agent.last_run_messages == [  
        ModelRequest(
            parts=[
                SystemPromptPart(
                    content='Providing a weather forecast at the locations the user provides.',
                ),
                UserPromptPart(
                    content='What will the weather be like in London on 2024-11-28?',
                    timestamp=IsNow(tz=timezone.utc),  
                ),
            ]
        ),
        ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='weather_forecast',
                    args=ArgsDict(
                        args_dict={
                            'location': 'a',
                            'forecast_date': '2024-01-01',  
                        }
                    ),
                    tool_call_id=None,
                )
            ],
            timestamp=IsNow(tz=timezone.utc),
        ),
        ModelRequest(
            parts=[
                ToolReturnPart(
                    tool_name='weather_forecast',
                    content='Sunny with a chance of rain',
                    tool_call_id=None,
                    timestamp=IsNow(tz=timezone.utc),
                ),
            ],
        ),
        ModelResponse(
            parts=[
                TextPart(
                    content='{"weather_forecast":"Sunny with a chance of rain"}',
                )
            ],
            timestamp=IsNow(tz=timezone.utc),
        ),
    ]
```

### Unit testing with `FunctionModel`

The above tests are a great start, but careful readers will notice that the `WeatherService.get_forecast` is never called since `TestModel` calls `weather_forecast` with a date in the past.

To fully exercise `weather_forecast`, we need to use [`FunctionModel`](https://ai.pydantic.dev/api/models/function/#pydantic_ai.models.function.FunctionModel) to customise how the tools is called.

Here's an example of using `FunctionModel` to test the `weather_forecast` tool with custom inputs

test\_weather\_app2.py

```python
import re

import pytest

from pydantic_ai import models
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    ToolCallPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from fake_database import DatabaseConn
from weather_app import run_weather_forecast, weather_agent

pytestmark = pytest.mark.anyio
models.ALLOW_MODEL_REQUESTS = False

def call_weather_forecast(  
    messages: list[ModelMessage], info: AgentInfo
) -> ModelResponse:
    if len(messages) == 1:
        # first call, call the weather forecast tool
        user_prompt = messages[0].parts[-1]
        m = re.search(r'\d{4}-\d{2}-\d{2}', user_prompt.content)
        assert m is not None
        args = {'location': 'London', 'forecast_date': m.group()}  
        return ModelResponse(
            parts=[ToolCallPart.from_raw_args('weather_forecast', args)]
        )
    else:
        # second call, return the forecast
        msg = messages[-1].parts[0]
        assert msg.part_kind == 'tool-return'
        return ModelResponse.from_text(f'The forecast is: {msg.content}')

async def test_forecast_future():
    conn = DatabaseConn()
    user_id = 1
    with weather_agent.override(model=FunctionModel(call_weather_forecast)):  
        prompt = 'What will the weather be like in London on 2032-01-01?'
        await run_weather_forecast([(prompt, user_id)], conn)

    forecast = await conn.get_forecast(user_id)
    assert forecast == 'The forecast is: Rainy with a chance of sun'
```

### Overriding model via pytest fixtures

If you're writing lots of tests that all require model to be overridden, you can use [pytest fixtures](https://docs.pytest.org/en/6.2.x/fixture.html) to override the model with [`TestModel`](https://ai.pydantic.dev/api/models/test/#pydantic_ai.models.test.TestModel) or [`FunctionModel`](https://ai.pydantic.dev/api/models/function/#pydantic_ai.models.function.FunctionModel) in a reusable way.

Here's an example of a fixture that overrides the model with `TestModel`:

tests.py

```python
import pytest
from weather_app import weather_agent

from pydantic_ai.models.test import TestModel

@pytest.fixture
def override_weather_agent():
    with weather_agent.override(model=TestModel()):
        yield

async def test_forecast(override_weather_agent: None):
    ...
    # test code here
```

## Evals

"Evals" refers to evaluating a models performance for a specific application.

Warning

Unlike unit tests, evals are an emerging art/science; anyone who claims to know for sure exactly how your evals should be defined can safely be ignored.

Evals are generally more like benchmarks than unit tests, they never "pass" although they do "fail"; you care mostly about how they change over time.

Since evals need to be run against the real model, then can be slow and expensive to run, you generally won't want to run them in CI for every commit.

### Measuring performance

The hardest part of evals is measuring how well the model has performed.

In some cases (e.g. an agent to generate SQL) there are simple, easy to run tests that can be used to measure performance (e.g. is the SQL valid? Does it return the right results? Does it return just the right results?).

In other cases (e.g. an agent that gives advice on quitting smoking) it can be very hard or impossible to make quantitative measures of performance — in the smoking case you'd really need to run a double-blind trial over months, then wait 40 years and observe health outcomes to know if changes to your prompt were an improvement.

There are a few different strategies you can use to measure performance:

- **End to end, self-contained tests** — like the SQL example, we can test the final result of the agent near-instantly
- **Synthetic self-contained tests** — writing unit test style checks that the output is as expected, checks like `'chewing gum' in response`, while these checks might seem simplistic they can be helpful, one nice characteristic is that it's easy to tell what's wrong when they fail
- **LLMs evaluating LLMs** — using another models, or even the same model with a different prompt to evaluate the performance of the agent (like when the class marks each other's homework because the teacher has a hangover), while the downsides and complexities of this approach are obvious, some think it can be a useful tool in the right circumstances
- **Evals in prod** — measuring the end results of the agent in production, then creating a quantitative measure of performance, so you can easily measure changes over time as you change the prompt or model used, [logfire](https://ai.pydantic.dev/logfire/) can be extremely useful in this case since you can write a custom query to measure the performance of your agent

### System prompt customization

The system prompt is the developer's primary tool in controlling an agent's behavior, so it's often useful to be able to customise the system prompt and see how performance changes. This is particularly relevant when the system prompt contains a list of examples and you want to understand how changing that list affects the model's performance.

Let's assume we have the following app for running SQL generated from a user prompt (this examples omits a lot of details for brevity, see the [SQL gen](https://ai.pydantic.dev/examples/sql-gen/) example for a more complete code):

sql\_app.py

```python
import json
from pathlib import Path
from typing import Union

from pydantic_ai import Agent, RunContext

from fake_database import DatabaseConn

class SqlSystemPrompt:  
    def __init__(
        self, examples: Union[list[dict[str, str]], None] = None, db: str = 'PostgreSQL'
    ):
        if examples is None:
            # if examples aren't provided, load them from file, this is the default
            with Path('examples.json').open('rb') as f:
                self.examples = json.load(f)
        else:
            self.examples = examples

        self.db = db

    def build_prompt(self) -> str:  
        return f"""\
Given the following {self.db} table of records, your job is to
write a SQL query that suits the user's request.

Database schema:
CREATE TABLE records (
  ...
);

{''.join(self.format_example(example) for example in self.examples)}
"""

    @staticmethod
    def format_example(example: dict[str, str]) -> str:  
        return f"""\
<example>
  <request>{example['request']}</request>
  <sql>{example['sql']}</sql>
</example>
"""

sql_agent = Agent(
    'gemini-1.5-flash',
    deps_type=SqlSystemPrompt,
)

@sql_agent.system_prompt
async def system_prompt(ctx: RunContext[SqlSystemPrompt]) -> str:
    return ctx.deps.build_prompt()

async def user_search(user_prompt: str) -> list[dict[str, str]]:
    """Search the database based on the user's prompts."""
    ...  
    result = await sql_agent.run(user_prompt, deps=SqlSystemPrompt())
    conn = DatabaseConn()
    return await conn.execute(result.data)
```

`examples.json` looks something like this:

```text
request: show me error records with the tag "foobar"
response: SELECT * FROM records WHERE level = 'error' and 'foobar' = ANY(tags)
```

examples.json

```json
{
  "examples": [
    {
      "request": "Show me all records",
      "sql": "SELECT * FROM records;"
    },
    {
      "request": "Show me all records from 2021",
      "sql": "SELECT * FROM records WHERE date_trunc('year', date) = '2021-01-01';"
    },
    {
      "request": "show me error records with the tag 'foobar'",
      "sql": "SELECT * FROM records WHERE level = 'error' and 'foobar' = ANY(tags);"
    },
    ...
  ]
}
```

Now we want a way to quantify the success of the SQL generation so we can judge how changes to the agent affect its performance.

We can use [`Agent.override`](https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.override) to replace the system prompt with a custom one that uses a subset of examples, and then run the application code (in this case `user_search`). We also run the actual SQL from the examples and compare the "correct" result from the example SQL to the SQL generated by the agent. (We compare the results of running the SQL rather than the SQL itself since the SQL might be semantically equivalent but written in a different way).

To get a quantitative measure of performance, we assign points to each run as follows: \* **\-100** points if the generated SQL is invalid \* **\-1** point for each row returned by the agent (so returning lots of results is discouraged) \* **+5** points for each row returned by the agent that matches the expected result

We use 5-fold cross-validation to judge the performance of the agent using our existing set of examples.

sql\_app\_evals.py

```python
import json
import statistics
from pathlib import Path
from itertools import chain

from fake_database import DatabaseConn, QueryError
from sql_app import sql_agent, SqlSystemPrompt, user_search

async def main():
    with Path('examples.json').open('rb') as f:
        examples = json.load(f)

    # split examples into 5 folds
    fold_size = len(examples) // 5
    folds = [examples[i : i + fold_size] for i in range(0, len(examples), fold_size)]
    conn = DatabaseConn()
    scores = []

    for i, fold in enumerate(folds, start=1):
        fold_score = 0
        # build all other folds into a list of examples
        other_folds = list(chain(*(f for j, f in enumerate(folds) if j != i)))
        # create a new system prompt with the other fold examples
        system_prompt = SqlSystemPrompt(examples=other_folds)

        # override the system prompt with the new one
        with sql_agent.override(deps=system_prompt):
            for case in fold:
                try:
                    agent_results = await user_search(case['request'])
                except QueryError as e:
                    print(f'Fold {i} {case}: {e}')
                    fold_score -= 100
                else:
                    # get the expected results using the SQL from this case
                    expected_results = await conn.execute(case['sql'])

                agent_ids = [r['id'] for r in agent_results]
                # each returned value has a score of -1
                fold_score -= len(agent_ids)
                expected_ids = {r['id'] for r in expected_results}

                # each return value that matches the expected value has a score of 3
                fold_score += 5 * len(set(agent_ids) & expected_ids)

        scores.append(fold_score)

    overall_score = statistics.mean(scores)
    print(f'Overall score: {overall_score:0.2f}')
    #> Overall score: 12.00
```

We can then change the prompt, the model, or the examples and see how the score changes over time.
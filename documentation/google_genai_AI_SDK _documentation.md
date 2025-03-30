---
title: "Google Gen AI SDK documentation"
source: "https://googleapis.github.io/python-genai/"
author:
published:
created: 2025-03-27
description:
tags:
  - "clippings"
---
## Models¶

The `client.models` modules exposes model inferencing and model getters.

## Generate Content¶

### with text content¶

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001', contents='Why is the sky blue?'
)
print(response.text)
```

### with uploaded file (Gemini Developer API only)¶

download the file in console.

```console
!wget -q https://storage.googleapis.com/generativeai-downloads/data/a11.txt
```

python code.

```python
file = client.files.upload(file='a11.txt')
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=['Could you summarize this file?', file]
)
print(response.text)
```

### How to structure contents argument for generate\_content[¶](https://googleapis.github.io/python-genai/#how-to-structure-contents-argument-for-generate-content "Link to this heading")

The SDK always converts the inputs to the contents argument into list\[types.Content\]. The following shows some common ways to provide your inputs.

#### Provide a list\[types.Content\][¶](https://googleapis.github.io/python-genai/#provide-a-list-types-content "Link to this heading")

This is the canonical way to provide contents, SDK will not do any conversion.

#### Provide a types.Content instance[¶](https://googleapis.github.io/python-genai/#provide-a-types-content-instance "Link to this heading")

```python
contents = types.Content(
role='user',
parts=[types.Part.from_text(text='Why is the sky blue?')]
)
```

SDK converts this to

```python
[
types.Content(
    role='user',
    parts=[types.Part.from_text(text='Why is the sky blue?')]
)
]
```

#### Provide a string¶

```python
contents='Why is the sky blue?'
```

The SDK will assume this is a text part, and it converts this into the following:

```python
[
types.UserContent(
    parts=[
    types.Part.from_text(text='Why is the sky blue?')
    ]
)
]
```

Where a types.UserContent is a subclass of types.Content, it sets the role field to be user.

#### Provide a list of string¶

The SDK assumes these are 2 text parts, it converts this into a single content, like the following:

```python
[
types.UserContent(
    parts=[
    types.Part.from_text(text='Why is the sky blue?'),
    types.Part.from_text(text='Why is the cloud white?'),
    ]
)
]
```

Where a types.UserContent is a subclass of types.Content, the role field in types.UserContent is fixed to be user.

#### Provide a function call part¶

```python
contents = types.Part.from_function_call(
name='get_weather_by_location',
args={'location': 'Boston'}
)
```

The SDK converts a function call part to a content with a model role:

```python
[
types.ModelContent(
    parts=[
    types.Part.from_function_call(
        name='get_weather_by_location',
        args={'location': 'Boston'}
    )
    ]
)
]
```

Where a types.ModelContent is a subclass of types.Content, the role field in types.ModelContent is fixed to be model.

#### Provide a list of function call parts¶

```python
contents = [
types.Part.from_function_call(
    name='get_weather_by_location',
    args={'location': 'Boston'}
),
types.Part.from_function_call(
    name='get_weather_by_location',
    args={'location': 'New York'}
),
]
```

The SDK converts a list of function call parts to the a content with a model role:

```python
[
types.ModelContent(
    parts=[
    types.Part.from_function_call(
        name='get_weather_by_location',
        args={'location': 'Boston'}
    ),
    types.Part.from_function_call(
        name='get_weather_by_location',
        args={'location': 'New York'}
    )
    ]
)
]
```

Where a types.ModelContent is a subclass of types.Content, the role field in types.ModelContent is fixed to be model.

#### Provide a non function call part¶

```python
contents = types.Part.from_uri(
file_uri: 'gs://generativeai-downloads/images/scones.jpg',
mime_type: 'image/jpeg',
)
```

The SDK converts all non function call parts into a content with a user role.

```python
[
types.UserContent(parts=[
    types.Part.from_uri(
    file_uri: 'gs://generativeai-downloads/images/scones.jpg',
    mime_type: 'image/jpeg',
    )
])
]
```

#### Provide a list of non function call parts¶

```python
contents = [
types.Part.from_text('What is this image about?'),
types.Part.from_uri(
    file_uri: 'gs://generativeai-downloads/images/scones.jpg',
    mime_type: 'image/jpeg',
)
]
```

The SDK will convert the list of parts into a content with a user role

```python
[
types.UserContent(
    parts=[
    types.Part.from_text('What is this image about?'),
    types.Part.from_uri(
        file_uri: 'gs://generativeai-downloads/images/scones.jpg',
        mime_type: 'image/jpeg',
    )
    ]
)
]
```

#### Mix types in contents¶

You can also provide a list of types.ContentUnion. The SDK leaves items of types.Content as is, it groups consecutive non function call parts into a single types.UserContent, and it groups consecutive function call parts into a single types.ModelContent.

If you put a list within a list, the inner list can only contain types.PartUnion items. The SDK will convert the inner list into a single types.UserContent.

## System Instructions and Other Configs¶

The output of the model can be influenced by several optional settings available in generate\_content’s config parameter. For example, the variability and length of the output can be influenced by the temperature and max\_output\_tokens respectively.

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='high',
    config=types.GenerateContentConfig(
        system_instruction='I say high, you say low',
        max_output_tokens=3,
        temperature=0.3,
    ),
)
print(response.text)
```

## Typed Config¶

All API methods support Pydantic types for parameters as well as dictionaries. You can get the type from `google.genai.types`.

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=types.Part.from_text(text='Why is the sky blue?'),
    config=types.GenerateContentConfig(
        temperature=0,
        top_p=0.95,
        top_k=20,
        candidate_count=1,
        seed=5,
        max_output_tokens=100,
        stop_sequences=['STOP!'],
        presence_penalty=0.0,
        frequency_penalty=0.0,
    ),
)

print(response.text)
```

## List Base Models¶

To retrieve tuned models, see: List Tuned Models

```python
for model in client.models.list():
    print(model)
```

```python
pager = client.models.list(config={'page_size': 10})
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

```python
async for job in await client.aio.models.list():
    print(job)
```

```python
async_pager = await client.aio.models.list(config={'page_size': 10})
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

## Safety Settings¶

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='Say something bad.',
    config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category='HARM_CATEGORY_HATE_SPEECH',
                threshold='BLOCK_ONLY_HIGH',
            )
        ]
    ),
)
print(response.text)
```

## Function Calling¶

You can pass a Python function directly and it will be automatically called and responded.

```python
def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
      location: The city and state, e.g. San Francisco, CA
    """
    return 'sunny'

response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='What is the weather like in Boston?',
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
    ),
)

print(response.text)
```

If you pass in a python function as a tool directly, and do not want automatic function calling, you can disable automatic function calling as follows:

With automatic function calling disabled, you will get a list of function call parts in the response:

If you don’t want to use the automatic function support, you can manually declare the function and invoke it.

The following example shows how to declare a function and pass it as a tool. Then you will receive a function call part in the response.

```python
function = types.FunctionDeclaration(
    name='get_current_weather',
    description='Get the current weather in a given location',
    parameters=types.Schema(
        type='OBJECT',
        properties={
            'location': types.Schema(
                type='STRING',
                description='The city and state, e.g. San Francisco, CA',
            ),
        },
        required=['location'],
    ),
)

tool = types.Tool(function_declarations=[function])

response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='What is the weather like in Boston?',
    config=types.GenerateContentConfig(
        tools=[tool],
    ),
)
print(response.function_calls[0])
```

After you receive the function call part from the model, you can invoke the function and get the function response. And then you can pass the function response to the model. The following example shows how to do it for a simple function invocation.

```python
user_prompt_content = types.Content(
    role='user',
    parts=[types.Part.from_text(text='What is the weather like in Boston?')],
)
function_call_part = response.function_calls[0]
function_call_content = response.candidates[0].content

try:
    function_result = get_current_weather(
        **function_call_part.function_call.args
    )
    function_response = {'result': function_result}
except (
    Exception
) as e:  # instead of raising the exception, you can let the model handle it
    function_response = {'error': str(e)}

function_response_part = types.Part.from_function_response(
    name=function_call_part.name,
    response=function_response,
)
function_response_content = types.Content(
    role='tool', parts=[function_response_part]
)

response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=[
        user_prompt_content,
        function_call_content,
        function_response_content,
    ],
    config=types.GenerateContentConfig(
        tools=[tool],
    ),
)

print(response.text)
```

If you configure function calling mode to be ANY, then the model will always return function call parts. If you also pass a python function as a tool, by default the SDK will perform automatic function calling until the remote calls exceed the maximum remote call for automatic function calling (default to 10 times).

If you’d like to disable automatic function calling in ANY mode:

```python
def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
        location: The city and state, e.g. San Francisco, CA
    """
    return "sunny"

response = client.models.generate_content(
    model="gemini-2.0-flash-001",
    contents="What is the weather like in Boston?",
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode='ANY')
        ),
    ),
)
```

If you’d like to set `x` number of automatic function call turns, you can configure the maximum remote calls to be `x + 1`. Assuming you prefer `1` turn for automatic function calling:

```python
def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
        location: The city and state, e.g. San Francisco, CA
    """
    return "sunny"

response = client.models.generate_content(
    model="gemini-2.0-flash-001",
    contents="What is the weather like in Boston?",
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            maximum_remote_calls=2
        ),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode='ANY')
        ),
    ),
)
```

## JSON Response Schema¶

Schemas can be provided as Pydantic Models.

```python
from pydantic import BaseModel

class CountryInfo(BaseModel):
    name: str
    population: int
    capital: str
    continent: str
    gdp: int
    official_language: str
    total_area_sq_mi: int

response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='Give me information for the United States.',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=CountryInfo,
    ),
)
print(response.text)
```

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='Give me information for the United States.',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema={
            'required': [
                'name',
                'population',
                'capital',
                'continent',
                'gdp',
                'official_language',
                'total_area_sq_mi',
            ],
            'properties': {
                'name': {'type': 'STRING'},
                'population': {'type': 'INTEGER'},
                'capital': {'type': 'STRING'},
                'continent': {'type': 'STRING'},
                'gdp': {'type': 'INTEGER'},
                'official_language': {'type': 'STRING'},
                'total_area_sq_mi': {'type': 'INTEGER'},
            },
            'type': 'OBJECT',
        },
    ),
)
print(response.text)
```

## Enum Response Schema¶

You can set response\_mime\_type to ‘text/x.enum’ to return one of those enum values as the response.

```python
from enum import Enum

class InstrumentEnum(Enum):
    PERCUSSION = 'Percussion'
    STRING = 'String'
    WOODWIND = 'Woodwind'
    BRASS = 'Brass'
    KEYBOARD = 'Keyboard'

response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='What instrument plays multiple notes at once?',
    config={
        'response_mime_type': 'text/x.enum',
        'response_schema': InstrumentEnum,
    },
)
print(response.text)
```

You can also set response\_mime\_type to ‘application/json’, the response will be identical but in quotes.

```python
class InstrumentEnum(Enum):
    PERCUSSION = 'Percussion'
    STRING = 'String'
    WOODWIND = 'Woodwind'
    BRASS = 'Brass'
    KEYBOARD = 'Keyboard'

response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents='What instrument plays multiple notes at once?',
    config={
        'response_mime_type': 'application/json',
        'response_schema': InstrumentEnum,
    },
)
print(response.text)
```

## Streaming¶

```python
for chunk in client.models.generate_content_stream(
    model='gemini-2.0-flash-001', contents='Tell me a story in 300 words.'
):
    print(chunk.text, end='')
```

If your image is stored in [Google Cloud Storage](https://cloud.google.com/storage), you can use the from\_uri class method to create a Part object.

```python
for chunk in client.models.generate_content_stream(
    model='gemini-2.0-flash-001',
    contents=[
        'What is this image about?',
        types.Part.from_uri(
            file_uri='gs://generativeai-downloads/images/scones.jpg',
            mime_type='image/jpeg',
        ),
    ],
):
    print(chunk.text, end='')
```

If your image is stored in your local file system, you can read it in as bytes data and use the `from_bytes` class method to create a `Part` object.

```python
YOUR_IMAGE_PATH = 'your_image_path'
YOUR_IMAGE_MIME_TYPE = 'your_image_mime_type'
with open(YOUR_IMAGE_PATH, 'rb') as f:
    image_bytes = f.read()

for chunk in client.models.generate_content_stream(
    model='gemini-2.0-flash-001',
    contents=[
        'What is this image about?',
        types.Part.from_bytes(data=image_bytes, mime_type=YOUR_IMAGE_MIME_TYPE),
    ],
):
    print(chunk.text, end='')
```

## Async¶

`client.aio` exposes all the analogous [async methods](https://docs.python.org/3/library/asyncio.html) that are available on `client`

For example, `client.aio.models.generate_content` is the `async` version of `client.models.generate_content`

```python
response = await client.aio.models.generate_content(
    model='gemini-2.0-flash-001', contents='Tell me a story in 300 words.'
)

print(response.text)
```

## Streaming¶

```python
async for chunk in await client.aio.models.generate_content_stream(
    model='gemini-2.0-flash-001', contents='Tell me a story in 300 words.'
):
    print(chunk.text, end='')
```

## Count Tokens and Compute Tokens¶

```python
response = client.models.count_tokens(
    model='gemini-2.0-flash-001',
    contents='why is the sky blue?',
)
print(response)
```

Compute tokens is only supported in Vertex AI.

```python
response = client.models.compute_tokens(
    model='gemini-2.0-flash-001',
    contents='why is the sky blue?',
)
print(response)
```

### Async¶

```python
response = await client.aio.models.count_tokens(
    model='gemini-2.0-flash-001',
    contents='why is the sky blue?',
)
print(response)
```

## Embed Content¶

```python
response = client.models.embed_content(
    model='text-embedding-004',
    contents='why is the sky blue?',
)
print(response)
```

```python
# multiple contents with config
response = client.models.embed_content(
    model='text-embedding-004',
    contents=['why is the sky blue?', 'What is your age?'],
    config=types.EmbedContentConfig(output_dimensionality=10),
)

print(response)
```

## Imagen¶

Support for generate image in Gemini Developer API is behind an allowlist

```python
# Generate Image
response1 = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt='An umbrella in the foreground, and a rainy night sky in the background',
    config=types.GenerateImagesConfig(
        number_of_images=1,
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response1.generated_images[0].image.show()
```

Upscale image is only supported in Vertex AI.

```python
# Upscale the generated image from above
response2 = client.models.upscale_image(
    model='imagen-3.0-generate-002',
    image=response1.generated_images[0].image,
    upscale_factor='x2',
    config=types.UpscaleImageConfig(
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response2.generated_images[0].image.show()
```

Edit image uses a separate model from generate and upscale.

Edit image is only supported in Vertex AI.

```python
# Edit the generated image from above
from google.genai.types import RawReferenceImage, MaskReferenceImage

raw_ref_image = RawReferenceImage(
    reference_id=1,
    reference_image=response1.generated_images[0].image,
)

# Model computes a mask of the background
mask_ref_image = MaskReferenceImage(
    reference_id=2,
    config=types.MaskReferenceConfig(
        mask_mode='MASK_MODE_BACKGROUND',
        mask_dilation=0,
    ),
)

response3 = client.models.edit_image(
    model='imagen-3.0-capability-001',
    prompt='Sunlight and clear sky',
    reference_images=[raw_ref_image, mask_ref_image],
    config=types.EditImageConfig(
        edit_mode='EDIT_MODE_INPAINT_INSERTION',
        number_of_images=1,
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response3.generated_images[0].image.show()
```

## Veo¶

Support for generate videos in Vertex and Gemini Developer API is behind an allowlist

```python
# Create operation
operation = client.models.generate_videos(
    model='veo-2.0-generate-001',
    prompt='A neon hologram of a cat driving at top speed',
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        fps=24,
        duration_seconds=5,
        enhance_prompt=True,
    ),
)

# Poll operation
while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)

video = operation.result.generated_videos[0].video
video.show()
```
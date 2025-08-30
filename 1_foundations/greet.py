import gradio as gr
import asyncio
import time

# ----------------------------
# Async version of greeting
# ----------------------------
async def async_greet(name):
    await asyncio.sleep(2)  # non-blocking wait
    return f"Hello, {name}! (async)"

# ----------------------------
# Sync version of greeting
# ----------------------------
def sync_greet(name):
    time.sleep(2)  # blocking wait
    return f"Hello, {name}! (sync)"

# ----------------------------
# Build Gradio app
# ----------------------------
with gr.Blocks() as demo:
    gr.Markdown("## Gradio Greeting App")

    name_input = gr.Textbox(label="Enter your name")
    async_output = gr.Textbox(label="Async Greeting")
    sync_output = gr.Textbox(label="Sync Greeting")

    # Async button
    gr.Button("Greet Async").click(async_greet, inputs=name_input, outputs=async_output)

    # Sync button
    gr.Button("Greet Sync").click(sync_greet, inputs=name_input, outputs=sync_output)

demo.launch()

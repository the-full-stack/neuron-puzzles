from modal import Image, Stub

stub = Stub(name="neuron-puzzles")

image = Image.debian_slim().pip_install("fastapi", "motor")

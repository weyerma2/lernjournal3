from flask import Flask, request, jsonify, send_file
import numpy as np
import onnxruntime
import cv2
import json

app = Flask(__name__, static_url_path='/', static_folder='web')

# Modelle vorbereiten
MODELS = {
    "EfficientNet-Lite4": "efficientnet-lite4-11.onnx",
    "EfficientNet-Lite4-int8": "efficientnet-lite4-11-int8.onnx",
    "EfficientNet-Lite4-qdq": "efficientnet-lite4-11-qdq.onnx",
}

SESSIONS = {name: onnxruntime.InferenceSession(path) for name, path in MODELS.items()}

# Labels laden
labels = json.load(open("labels_map.txt", "r"))

# Preprocessing Funktionen
def pre_process_edgetpu(img, dims):
    output_height, output_width, _ = dims
    img = resize_with_aspectratio(img, output_height, output_width)
    img = center_crop(img, output_height, output_width)
    img = np.asarray(img, dtype='float32')
    img -= [127.0, 127.0, 127.0]
    img /= [128.0, 128.0, 128.0]
    return img

def resize_with_aspectratio(img, out_height, out_width, scale=87.5, inter_pol=cv2.INTER_LINEAR):
    height, width, _ = img.shape
    new_height = int(100. * out_height / scale)
    new_width = int(100. * out_width / scale)
    if height > width:
        w = new_width
        h = int(new_height * height / width)
    else:
        h = new_height
        w = int(new_width * width / height)
    return cv2.resize(img, (w, h), interpolation=inter_pol)

def center_crop(img, out_height, out_width):
    height, width, _ = img.shape
    left = int((width - out_width) / 2)
    right = int((width + out_width) / 2)
    top = int((height - out_height) / 2)
    bottom = int((height + out_height) / 2)
    return img[top:bottom, left:right]

@app.route("/")
def indexPage():
    return send_file("web/index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    content = request.files.get('0', '').read()
    img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_UNCHANGED)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = pre_process_edgetpu(img, (224, 224, 3))
    img_batch = np.expand_dims(img, axis=0)

    results_all = {}

    for model_name, session in SESSIONS.items():
        # ONNX Runtime expects exact input/output names
        try:
            result = session.run(["Softmax:0"], {"images:0": img_batch})[0]
        except Exception:
            result = session.run(None, {"images:0": img_batch})[0]

        top_indices = result[0].argsort()[-3:][::-1]
        results_all[model_name] = [
            {"class": labels[str(i)], "value": float(result[0][i])}
            for i in top_indices
        ]

    return jsonify(results_all)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

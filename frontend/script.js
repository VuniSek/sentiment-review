const API_URL = window.API_URL || "http://127.0.0.1:8000/predict-csv";

const form = document.getElementById("uploadForm");
const progressBar = document.getElementById("progressBar");
const statusText = document.getElementById("status");

form.addEventListener("submit", function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Pilih file terlebih dahulu");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();

    xhr.open("POST", API_URL, true);
    xhr.responseType = "blob";

    xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            progressBar.style.width = percent + "%";
            statusText.innerText = `Upload ${Math.round(percent)}%`;
        }
    };

    xhr.onload = function () {
        if (xhr.status === 200) {
            const blob = xhr.response;
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = "hasil_prediksi.csv";
            document.body.appendChild(a);
            a.click();
            a.remove();

            statusText.innerText = "Selesai ✔ File berhasil diproses";
            progressBar.style.width = "100%";
        } else {
            statusText.innerText = "Gagal memproses file ❌";
        }
    };

    xhr.onerror = function () {
        statusText.innerText = "Koneksi ke server gagal ❌";
    };

    xhr.send(formData);
});

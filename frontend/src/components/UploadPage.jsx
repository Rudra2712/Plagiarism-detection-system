import React, { useState } from "react";
import api from "../api";

export default function UploadPage({
  onUploaded,
  onResults,
  onClearResults,
  uploadInfo,
}) {
  const [assignment, setAssignment] = useState(
    uploadInfo?.assignment || "AssignmentUpload"
  );
  const [fileCount, setFileCount] = useState(1);
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  function handleFileChange(index, e) {
    const updated = [...files];
    updated[index] = e.target.files[0];
    setFiles(updated);
  }

  async function onUpload() {
    if (files.length === 0 || files.some((f) => !f)) {
      setMessage("Please select all files to upload");
      return;
    }
    for (const f of files) {
      if (!f.name.toLowerCase().endsWith(".cpp")) {
        setMessage("Only .cpp files are allowed");
        return;
      }
    }

    const form = new FormData();
    for (const f of files) form.append("files", f);
    form.append("assignment", assignment);

    setBusy(true);
    setMessage("Uploading...");
    try {
      const res = await api.post("/api/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onUploaded?.(res.data);
      setMessage("Upload successful");
    } catch (err) {
      console.error(err);
      setMessage(err?.response?.data?.error || "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onCheck() {
    setBusy(true);
    setMessage("Running check...");
    try {
      const res = await api.post("/api/check");
      onResults?.(res.data);
      setMessage("Check complete");
    } catch (err) {
      console.error(err);
      setMessage(err?.response?.data?.error || "Check failed");
    } finally {
      setBusy(false);
    }
  }

  async function onRerun() {
    await onCheck();
  }

  async function onCleanup() {
    setBusy(true);
    setMessage("Cleaning up...");
    try {
      await api.post("/api/cleanup");
      onUploaded?.(null);
      onResults?.(null);
      setFiles([]);
      setMessage("Cleanup complete");
    } catch (err) {
      console.error(err);
      setMessage(err?.response?.data?.error || "Cleanup failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mb-6 ">
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Upload C++ Files</h2>
          <p className="card-subtitle">All files are accepted</p>
        </div>

        <div className="card-body space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              className="input"
              value={assignment}
              onChange={(e) => setAssignment(e.target.value)}
              placeholder="Assignment name"
            />

            <div className="flex items-center gap-2">
              <label className="font-medium">Files:</label>
              <input
                type="number"
                min="1"
                max="20"
                value={fileCount}
                onChange={(e) => {
                  const n = Math.max(
                    1,
                    Math.min(20, parseInt(e.target.value || "1"))
                  );
                  setFileCount(n);
                  setFiles(new Array(n).fill(null));
                }}
                className="input w-24"
              />
            </div>
          </div>

          <div className="file-grid">
            {Array.from({ length: fileCount }).map((_, i) => (
              <label key={i} className="file-item">
                <span className="file-label">File {i + 1}</span>
                <input
                  type="file"
                  accept=".cpp"
                  onChange={(e) => handleFileChange(i, e)}
                />
              </label>
            ))}
          </div>

          <div className="actions">
            <button
              className="btn btn-primary"
              onClick={onUpload}
              disabled={busy}
            >
              Upload
            </button>
            <button
              className="btn btn-success"
              onClick={onCheck}
              disabled={busy}
            >
              Run Check
            </button>
            <button
              className="btn btn-warning"
              onClick={onRerun}
              disabled={busy}
            >
              Re-run
            </button>
            <button
              className="btn btn-danger"
              onClick={() => onClearResults?.()}
              disabled={busy}
            >
              Clear Results
            </button>
            <button
              className="btn btn-muted"
              onClick={onCleanup}
              disabled={busy}
            >
              Cleanup
            </button>
          </div>

          {message && <div className="status-text">{message}</div>}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";

type EncodeResult = {
  job_id: string;
  original_name: string;
  sha256: string;
  source_bytes: number;
  dna_length: number;
  dna_preview: string;
  ecc: string;
};

type DecodeResult = {
  job_id: string;
  original_name: string;
  reconstructed: string;
  sha256: string;
  verified: boolean;
  coding: number;
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [useEcc, setUseEcc] = useState(false);
  const [busy, setBusy] = useState(false);
  const [encoded, setEncoded] = useState<EncodeResult | null>(null);
  const [decoded, setDecoded] = useState<DecodeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [dnaFile, setDnaFile] = useState<File | null>(null);
  const [dnaBusy, setDnaBusy] = useState(false);
  const [dnaError, setDnaError] = useState<string | null>(null);
  const [dnaSuccess, setDnaSuccess] = useState<string | null>(null);
  const [dnaCoding, setDnaCoding] = useState<number | null>(null);

  async function encode() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setEncoded(null);
    setDecoded(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const ecc = useEcc ? "rep3" : "none";
      const r = await fetch(`/api/encode?ecc=${ecc}`, { method: "POST", body: fd });
      if (!r.ok) throw new Error((await r.json()).detail ?? r.statusText);
      setEncoded(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function decodeJob() {
    if (!encoded) return;
    setBusy(true);
    setError(null);
    try {
      const r = await fetch(`/api/decode/${encoded.job_id}`, { method: "POST" });
      if (!r.ok) throw new Error((await r.json()).detail ?? r.statusText);
      const data = await r.json();
      setDecoded({ ...data, coding: data.coding ?? 0 });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function decodeFile() {
    if (!dnaFile) return;
    setDnaBusy(true);
    setDnaError(null);
    setDnaSuccess(null);
    setDnaCoding(null);
    try {
      const fd = new FormData();
      fd.append("file", dnaFile);
      const r = await fetch("/api/decode-file", { method: "POST", body: fd });

      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.detail ?? r.statusText);
      }

      const codingHeader = r.headers.get("x-coding");
      if (codingHeader !== null) {
        setDnaCoding(parseInt(codingHeader, 10));
      }

      const cd = r.headers.get("content-disposition") ?? "";
      const match = /filename="?([^"]+)"?/.exec(cd);
      const outName = match ? match[1] : "decoded.bin";

      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = outName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);

      setDnaSuccess(`Downloaded: ${outName} — check your Downloads folder.`);
    } catch (e) {
      setDnaError(e instanceof Error ? e.message : String(e));
    } finally {
      setDnaBusy(false);
    }
  }

  return (
    <main>
      <h1>NucleoStore</h1>
      <p className="tagline">DNA-based digital data storage</p>

      <div className="card">
        <h2>1. Upload &amp; Encode</h2>
        <div className="row">
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={busy}
          />
          <label style={{ display: "flex", alignItems: "center", gap: 8, color: "#cbd5e1", fontSize: 14 }}>
            <input
              type="checkbox"
              checked={useEcc}
              onChange={(e) => setUseEcc(e.target.checked)}
              disabled={busy}
            />
            Error correction (3×)
          </label>
          <button onClick={encode} disabled={!file || busy}>
            {busy ? "Working…" : "Encode to DNA"}
          </button>
        </div>

        {encoded && (
          <>
            <dl className="kv">
              <dt>Job ID</dt><dd>{encoded.job_id}</dd>
              <dt>File</dt><dd>{encoded.original_name}</dd>
              <dt>Size</dt><dd>{encoded.source_bytes.toLocaleString()} bytes</dd>
              <dt>DNA length</dt><dd>{encoded.dna_length.toLocaleString()} nucleotides</dd>
              <dt>ECC</dt><dd>{encoded.ecc}</dd>
              <dt>SHA-256</dt><dd>{encoded.sha256}</dd>
            </dl>
            <div className="dna-preview">{encoded.dna_preview}…</div>
            <div className="downloads">
              <a href={`/api/dna/${encoded.job_id}`} download>Download .dna</a>
              <a href={`/api/original/${encoded.job_id}`} download>Download original</a>
            </div>
          </>
        )}
      </div>

      {encoded && (
        <div className="card">
          <h2>2. Decode This Job</h2>
          <div className="row">
            <button onClick={decodeJob} disabled={busy}>
              {busy ? "Working…" : "Decode from stored DNA"}
            </button>
          </div>
          {decoded && (
            <>
              <div className={`status ${decoded.verified ? "ok" : "err"}`}>
                {decoded.verified
                  ? "✓ SHA-256 match — reconstructed file is identical"
                  : "✗ SHA-256 mismatch — reconstruction differs"}
              </div>
              <dl className="kv">
                <dt>SHA-256</dt><dd>{decoded.sha256}</dd>
                <dt>Error correction</dt>
                <dd>
                  {decoded.coding === 1
                    ? "3× repetition (rep3) — corrupted bases auto-corrected"
                    : "none"}
                </dd>
              </dl>
              <div className="downloads">
                <a href={`/api/reconstructed/${decoded.job_id}`} download>
                  Download reconstructed file
                </a>
              </div>
            </>
          )}
        </div>
      )}

      <div className="card">
        <h2>3. Upload a .dna File → Get Original Back</h2>
        <p style={{ color: "#94a3b8", fontSize: 13, marginBottom: 12 }}>
          Any self-contained .dna file — including one from another machine.
          If the file was encoded with error correction, corrupted bases are
          automatically repaired.
        </p>
        <div className="row">
          <input
            type="file"
            accept=".dna,text/plain"
            onChange={(e) => setDnaFile(e.target.files?.[0] ?? null)}
            disabled={dnaBusy}
          />
          <button onClick={decodeFile} disabled={!dnaFile || dnaBusy}>
            {dnaBusy ? "Decoding…" : "Decode & Download"}
          </button>
        </div>
        {dnaSuccess && (
          <div className="status ok">
            {dnaSuccess}
            {dnaCoding === 1 && " — 3× repetition ECC was applied"}
            {dnaCoding === 0 && " — no error correction (plain encoding)"}
          </div>
        )}
        {dnaError && <div className="status err">{dnaError}</div>}
      </div>

      {error && <div className="status err">{error}</div>}
    </main>
  );
}
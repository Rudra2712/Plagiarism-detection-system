import React from "react";

export default function ResultsPage({ results, onClear }) {
  if (!results) return null;

  const details = results?.results?.details || [];
  const suspicious = results?.results?.suspiciousPairs || [];

  // Extract just the filename from a full path
  const getFileName = (path) => (path ? path.split(/[\\/]/).pop() : "");

  // Find highest similarity
  let maxPair = null;
  let maxScore = 0;
  details.forEach((d) => {
    [...(d.topAtoB || []), ...(d.topBtoA || [])].forEach((m) => {
      const score = Number(m.similarityPct) || 0;
      if (score > maxScore) {
        maxScore = score;
        maxPair = [getFileName(m.left), getFileName(m.right)];
      }
      m.similarityPct = score;
    });
  });

  return (
    <div className="space-y-8 p-6 bg-slate-950 min-h-screen text-gray-200 mb-6 ">
      {/* 🔥 Highest Plagiarism */}
      {maxPair && (
        <div className="p-4 bg-red-900/40 border border-red-700 rounded-2xl shadow-md">
          <h3 className="text-xl font-semibold text-red-300 mb-2 flex items-center gap-2">
            🚨 Highest Plagiarism Detected
          </h3>
          <p className="text-gray-200">
            Between <span className="font-semibold text-white text-lg">{maxPair[0]}</span> and{" "}
            <span className="font-semibold text-white text-lg">{maxPair[1]}</span> —{" "}
            <span className="text-red-400 font-bold">{maxScore.toFixed(2)}%</span> similarity.
          </p>
        </div>
      )}

      {/* 🧩 Debug Section */}
      <details className="bg-slate-800 rounded-xl p-3 border border-slate-700">
        <summary className="cursor-pointer text-gray-400 hover:text-gray-300">
          🧩 Show Raw Results (Debug)
        </summary>
        <pre className="mt-3 text-xs overflow-auto max-h-80 text-gray-300 bg-slate-900 p-4 rounded-lg">
          {JSON.stringify(results, null, 2)}
        </pre>
      </details>

      {/* ⚠️ Suspicious Pairs */}
      <div className="bg-slate-800 p-4 border border-slate-700 rounded-2xl shadow-md">
        <div className="p-5 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white">Suspicious Assignment Pairs</h2>
          <p className="text-gray-400 text-sm">Pairs exceeding configured thresholds</p>
        </div>
        <div className="p-5">
          
          {suspicious.length === 0 ? (
            <div className="text-gray-500 italic">(none)</div>
          ) : (
            <ul className="list-disc ml-6 space-y-1">
              {suspicious.map((p, idx) => (
                <li key={idx} className="text-gray-300">
                  <span className="font-medium">{getFileName(p[0])}</span>{" "}
                  <span className="text-slate-500">↔</span>{" "}
                  <span className="font-medium">{getFileName(p[1])}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* 📋 Detailed Tables */}
      {details.map((d, i) => (
        <div key={i} className="bg-slate-800 border border-slate-700 rounded-2xl shadow-md p-4">
          <div className="p-5 border-b border-slate-700">
            <h3 className="text-lg font-semibold text-white">
              Details: {getFileName(d.pair[0])} ↔ {getFileName(d.pair[1])}
            </h3>
          </div>

          <div className="p-5 grid md:grid-cols-2 gap-6">
            {/* A→B Table */}
            <div>
              <h4 className="text-md font-semibold text-sky-400 mb-3">Top matches A → B</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border border-slate-700 rounded-lg overflow-hidden">
                  <thead className="bg-slate-700 text-gray-300">
                    <tr>
                      <th className="px-3 py-2 text-left">Left</th>
                      <th className="px-3 py-2 text-center">Similarity</th>
                      <th className="px-3 py-2 text-right">Right</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(d.topAtoB || []).map((r, idx) => (
                      <tr
                        key={idx}
                        className={`border-b border-slate-700 hover:bg-slate-700/50 ${
                          r.similarityPct === maxScore ? "bg-red-800/40" : ""
                        }`}
                      >
                        <td className="px-3 py-2 text-gray-300">{getFileName(r.left)}</td>
                        <td className="px-3 py-2 text-center font-semibold text-white">
                          {r.similarityPct.toFixed(2)}%
                        </td>
                        <td className="px-3 py-2 text-right text-gray-300">{getFileName(r.right)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* B→A Table */}
            <div>
              <h4 className="text-md font-semibold text-sky-400 mb-3">Top matches B → A</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border border-slate-700 rounded-lg overflow-hidden">
                  <thead className="bg-slate-700 text-gray-300">
                    <tr>
                      <th className="px-3 py-2 text-left">Left</th>
                      <th className="px-3 py-2 text-center">Similarity</th>
                      <th className="px-3 py-2 text-right">Right</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(d.topBtoA || []).map((r, idx) => (
                      <tr
                        key={idx}
                        className={`border-b border-slate-700 hover:bg-slate-700/50 ${
                          r.similarityPct === maxScore ? "bg-red-800/40" : ""
                        }`}
                      >
                        <td className="px-3 py-2 text-gray-300">{getFileName(r.left)}</td>
                        <td className="px-3 py-2 text-center font-semibold text-white">
                          {r.similarityPct.toFixed(2)}%
                        </td>
                        <td className="px-3 py-2 text-right text-gray-300">{getFileName(r.right)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

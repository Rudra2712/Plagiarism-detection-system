import React from "react";

export default function ResultsPage({ results }) {
  if (!results) return null;

  const details = results?.results?.details || [];
  const suspicious = results?.results?.suspiciousPairs || [];

  // Find the highest similarity from all pairs
  let maxPair = null;
  let maxScore = 0;
  details.forEach((d) => {
    [...(d.topAtoB || []), ...(d.topBtoA || [])].forEach((m) => {
      if (m.similarityPct > maxScore) {
        maxScore = m.similarityPct;
        maxPair = [m.left, m.right];
      }
    });
  });

  return (
    <div className="space-y-6">
      {maxPair && (
        <div className="notice danger">
          <h3 className="notice-title">Highest Plagiarism Detected</h3>
          <p className="notice-text">
            Between <strong>{maxPair[0]}</strong> and <strong>{maxPair[1]}</strong> —
            <span className="highlight"> {maxScore.toFixed(2)}%</span> similarity.
          </p>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Suspicious Assignment Pairs</h2>
          <p className="card-subtitle">Pairs exceeding configured thresholds</p>
        </div>
        <div className="card-body">
          {suspicious.length === 0 ? (
            <div className="muted">(none)</div>
          ) : (
            <ul className="list-disc ml-6">
              {suspicious.map((p, idx) => (
                <li key={idx}>
                  {p[0]} ↔ {p[1]}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {details.map((d, i) => (
        <div key={i} className="card">
          <div className="card-header">
            <div className="card-title">Details: {d.pair[0]} ↔ {d.pair[1]}</div>
          </div>
          <div className="card-body grid md:grid-cols-2 gap-4">
            <div>
              <div className="section-title">Top matches A→B</div>
              <table className="table">
                <thead>
                  <tr>
                    <th>Left</th>
                    <th>Similarity</th>
                    <th>Right</th>
                  </tr>
                </thead>
                <tbody>
                  {(d.topAtoB || []).map((r, idx) => (
                    <tr key={idx} className={r.similarityPct === maxScore ? "row-hot" : ""}>
                      <td>{r.left}</td>
                      <td>{r.similarityPct.toFixed(2)}%</td>
                      <td>{r.right}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <div className="section-title">Top matches B→A</div>
              <table className="table">
                <thead>
                  <tr>
                    <th>Left</th>
                    <th>Similarity</th>
                    <th>Right</th>
                  </tr>
                </thead>
                <tbody>
                  {(d.topBtoA || []).map((r, idx) => (
                    <tr key={idx} className={r.similarityPct === maxScore ? "row-hot" : ""}>
                      <td>{r.left}</td>
                      <td>{r.similarityPct.toFixed(2)}%</td>
                      <td>{r.right}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

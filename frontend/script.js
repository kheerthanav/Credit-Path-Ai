// ---------- SINGLE PREDICTION ----------
document.getElementById("predictionForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const data = {
    loan_amount: Number(document.getElementById("loan_amount").value || 0),
    monthly_income: Number(document.getElementById("monthly_income").value || 0),
    interest_rate: Number(document.getElementById("interest_rate").value || 0),
    age: Number(document.getElementById("age").value || 0),
    credit_score: Number(document.getElementById("credit_score").value || 600),
    active_loans_count: Number(document.getElementById("active_loans").value || 0),
    past_due_days: Number(document.getElementById("past_due_days").value || 0),
    loan_purpose: document.getElementById("loan_purpose").value || ''
  };

  try {
    const res = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(data)
    });

    if (!res.ok) {
      const text = await res.text();
      document.getElementById("singleResult").hidden = false;
      document.getElementById("singleAction").innerText = "Server error";
      document.getElementById("singleExplain").innerText = text;
      return;
    }

    const json = await res.json();

    document.getElementById("singleResult").hidden = false;
    document.getElementById("singleBorrower").innerText = `Borrower: —`;
    document.getElementById("singleProbability").innerText = `Probability: ${(json.result.probability * 100).toFixed(2)}%`;
    document.getElementById("singleAction").innerText = `Action: ${json.result.action}`;
    document.getElementById("singleExplain").innerText = JSON.stringify(json.result.explanation, null, 2);
  } catch (err) {
    document.getElementById("singleResult").hidden = false;
    document.getElementById("singleAction").innerText = "Network error";
    document.getElementById("singleExplain").innerText = String(err);
  }
});

// ---------- MANUAL BATCH FORM GENERATION ----------
const createBatchBtn = document.getElementById("createBatchBtn");
const batchCountInput = document.getElementById("batchCount");
const batchFormsContainer = document.getElementById("batchFormsContainer");
const sendBatchBtn = document.getElementById("sendBatchBtn");
const batchResultsSection = document.getElementById("batchResultSection");
const batchResultsBody = document.getElementById("batchResultsBody");

createBatchBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  const count = parseInt(batchCountInput.value) || 0;
  batchFormsContainer.innerHTML = "";
  batchResultsSection.style.display = "none";
  batchResultsBody.innerHTML = "";
  document.getElementById("batchResult").innerText = "";

  if (count <= 0 || count > 50) {
    alert("Enter a number between 1 and 50.");
    return;
  }

  for (let i = 0; i < count; i++) {
    const idx = i + 1;
    const row = document.createElement("div");
    row.className = "batch-row";
    row.style = "border:1px solid #eef2ff;padding:10px;margin-bottom:10px;border-radius:8px;";

    row.innerHTML = `
      <h4>Test ${idx}</h4>
      <label>Loan Amount</label><input type="number" class="b-loan_amount" value="0">
      <label>Monthly Income</label><input type="number" class="b-monthly_income" value="0">
      <label>Interest Rate (%)</label><input type="number" step="0.01" class="b-interest_rate" value="0">
      <label>Age</label><input type="number" class="b-age" value="30">
      <label>Credit Score</label><input type="number" class="b-credit_score" value="650">
      <label>Active Loans Count</label><input type="number" class="b-active_loans_count" value="0">
      <label>Past Due Days</label><input type="number" class="b-past_due_days" value="0">
      <label>Loan Purpose</label>
      <select class="b-loan_purpose">
        <option value="">Select</option>
        <option value="home">Home</option>
        <option value="education">Education</option>
        <option value="business">Business</option>
        <option value="personal">Personal</option>
        <option value="medical">Medical</option>
        <option value="auto">Auto</option>
      </select>
    `;

    batchFormsContainer.appendChild(row);
  }

  sendBatchBtn.style.display = "inline-block";
});

// ---------- SEND BATCH ----------
async function sendBatch() {
  const rows = Array.from(batchFormsContainer.querySelectorAll(".batch-row"));
  if (!rows.length) {
    alert("Create forms first.");
    return;
  }

  // build array of feature dicts
  const payload = rows.map((r) => {
    return {
      loan_amount: Number(r.querySelector(".b-loan_amount").value || 0),
      monthly_income: Number(r.querySelector(".b-monthly_income").value || 0),
      interest_rate: Number(r.querySelector(".b-interest_rate").value || 0),
      age: Number(r.querySelector(".b-age").value || 0),
      credit_score: Number(r.querySelector(".b-credit_score").value || 600),
      active_loans_count: Number(r.querySelector(".b-active_loans_count").value || 0),
      past_due_days: Number(r.querySelector(".b-past_due_days").value || 0),
      loan_purpose: r.querySelector(".b-loan_purpose").value || ''
    };
  });

  // send to backend
  try {
    const res = await fetch("/batch_manual_predict", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const txt = await res.text();
      document.getElementById("batchResult").innerText = "Server error: " + txt;
      return;
    }

    const results = await res.json(); // expected list of { index, result: {probability, action, explanation} }

    // render table (option B)
    batchResultsBody.innerHTML = "";
    results.forEach((r, i) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="padding:8px;border:1px solid #e6eef7">${i+1}</td>
        <td style="padding:8px;border:1px solid #e6eef7">${(r.result.probability*100).toFixed(2)}%</td>
        <td style="padding:8px;border:1px solid #e6eef7">${r.result.action}</td>
        <td style="padding:8px;border:1px solid #e6eef7"><pre style="margin:0">${JSON.stringify(r.result.explanation)}</pre></td>
      `;
      batchResultsBody.appendChild(tr);
    });

    batchResultsSection.style.display = "block";
    document.getElementById("batchResult").innerText = "Batch processed: " + results.length + " items.";
  } catch (err) {
    document.getElementById("batchResult").innerText = "Network error: " + String(err);
  }
}

sendBatchBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  sendBatch();
});

// expose for HTML safety (not strictly necessary now)
window.sendBatch = sendBatch;

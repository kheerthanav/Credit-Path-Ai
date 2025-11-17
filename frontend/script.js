// -----------------------
// SINGLE PREDICTION
// -----------------------
document.getElementById("predictionForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
        loan_amount: document.getElementById("loan_amount").value,
        monthly_income: document.getElementById("monthly_income").value,
        interest_rate: document.getElementById("interest_rate").value,
        age: document.getElementById("age").value,
        credit_score: document.getElementById("credit_score").value,
        active_loans_count: document.getElementById("active_loans").value,
        past_due_days: document.getElementById("past_due_days").value,
        loan_purpose: document.getElementById("loan_purpose").value
    };

    const res = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(data),
    });

    const result = await res.json();

    document.getElementById("result").innerText =
        result?.result?.action
            ? `Probability: ${result.result.probability}\nAction: ${result.result.action}`
            : "Error.";
});


// -----------------------
// BATCH UPLOAD
// -----------------------
async function uploadBatch() {
    const fileInput = document.getElementById("batchFile").files[0];

    if (!fileInput) {
        alert("Please upload a CSV file first.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput);

    const res = await fetch("/batch_predict", {
        method: "POST",
        credentials: "include",
        body: formData,
    });

    const data = await res.json();

    document.getElementById("batchResult").innerText =
        data?.status === "success" ? "Batch Prediction Complete!" : "Error processing file.";
}


// -----------------------
// SIGNUP
// -----------------------
async function signup() {
    const payload = {
        name: document.getElementById('signName')?.value,
        email: document.getElementById('signEmail')?.value,
        password: document.getElementById('signPassword')?.value
    };

    const res = await fetch("/signup", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    document.getElementById('signMsg').innerText = data.message || data.error;

    if (data.status === "success") {
        setTimeout(() => window.location.href = "/login.html", 800);
    }
}


// -----------------------
// LOGIN
// -----------------------
async function login() {
    const payload = {
        email: document.getElementById('loginEmail')?.value,
        password: document.getElementById('loginPassword')?.value
    };

    const res = await fetch("/login", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    document.getElementById('loginMsg').innerText = data.message || data.error;

    if (data.message === "Login successful") {
        setTimeout(() => window.location.href = "/dashboard", 700);
    }
}


// -----------------------
// MAKE FUNCTIONS GLOBAL
// -----------------------
window.uploadBatch = uploadBatch;
window.signup = signup;
window.login = login;

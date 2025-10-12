import requests, json

payload = {
  "borrowers": [
    {"name":"Ramesh Kumar","email":"ramesh.kumar@corporate.com","income":120000,"loan_amount":30000,"credit_score":720,"employment_years":6,"purpose":"home renovation"},
    {"name":"Scammer Joe","email":"joe@quickloan.xyz","income":15000,"loan_amount":50000,"credit_score":480,"employment_years":0.2,"purpose":"urgent cash"},
    {"name":"Incomplete","email":"bad-email","income":None,"loan_amount":2000,"credit_score":400,"employment_years":1,"purpose":"business"},
    {"name":"Priya Sharma","email":"priya@gmail.com","income":80000,"loan_amount":10000,"credit_score":810,"employment_years":12,"purpose":"education"},
    {"name":"Maya","email":"maya@offers.club","income":30000,"loan_amount":35000,"credit_score":650,"employment_years":0.3,"purpose":"investment opportunity"}
  ]
}

r = requests.post("http://localhost:8000/predict", json=payload)
print("Status:", r.status_code)
print(json.dumps(r.json(), indent=2))

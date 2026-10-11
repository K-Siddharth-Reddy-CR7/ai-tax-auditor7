import os
import json
import re
import math
import time
from collections import Counter
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load datasets
def load_json_file(filename):
    paths = [
        os.path.join(BASE_DIR, filename),
        os.path.join(BASE_DIR, "Datasets", filename),
        filename
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    print(f"Warning: {filename} not found!")
    return []

PRODUCTS = load_json_file("products.json")
TAXES = load_json_file("taxes.json")
TRADE_POLICIES = load_json_file("trade_policies.json")
SAMPLE_TRANSACTIONS = load_json_file("sample_transactions.json")

print(f"Loaded {len(PRODUCTS)} products, {len(TAXES)} tax entries, {len(TRADE_POLICIES)} policies, {len(SAMPLE_TRANSACTIONS)} sample transactions.")

# Currency exchange rates to USD (approximate reference rates for display)
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "INR": 83.5,
    "GBP": 0.79,
    "JPY": 155.0,
    "CAD": 1.36,
    "AUD": 1.52,
    "SGD": 1.35,
    "CHF": 0.90,
    "CNY": 7.24,
    "BRL": 5.35,
    "AED": 3.67,
    "SAR": 3.75,
    "KRW": 1370.0,
    "MXN": 17.1,
    "ZAR": 18.5,
    "SEK": 10.6,
    "NOK": 10.7,
    "NZD": 1.64,
    "TRY": 32.2,
    "PLN": 3.95,
    "THB": 36.8,
    "IDR": 16200.0,
    "MYR": 4.71,
    "PHP": 58.2,
    "VND": 25400.0,
}

# --- TF-IDF RAG / Semantic Policy Retriever ---
def tokenize(text):
    return re.findall(r'\w+', (text or "").lower())

class PolicyRetriever:
    def __init__(self, policies):
        self.policies = policies
        self.doc_tokens = []
        self.df = Counter()
        self.doc_vectors = []
        
        for p in policies:
            text = f"{p.get('Country', '')} {p.get('Category', '')} {p.get('Policy_Summary', '')} {p.get('Compliance_Note', '')}"
            tokens = tokenize(text)
            self.doc_tokens.append(tokens)
            unique_terms = set(tokens)
            for t in unique_terms:
                self.df[t] += 1
                
        self.N = len(policies) or 1
        self.idf = {term: math.log((self.N + 1) / (freq + 1)) + 1 for term, freq in self.df.items()}

        for tokens in self.doc_tokens:
            tf = Counter(tokens)
            norm = 0.0
            vec = {}
            for term, count in tf.items():
                weight = count * self.idf.get(term, 1.0)
                vec[term] = weight
                norm += weight ** 2
            norm = math.sqrt(norm) or 1.0
            for term in vec:
                vec[term] /= norm
            self.doc_vectors.append(vec)

    def retrieve(self, query, top_k=3, country_filter=None, category_filter=None):
        q_tokens = tokenize(query)
        if not q_tokens:
            return self.policies[:top_k]

        q_tf = Counter(q_tokens)
        q_vec = {}
        q_norm = 0.0
        for term, count in q_tf.items():
            weight = count * self.idf.get(term, 1.0)
            q_vec[term] = weight
            q_norm += weight ** 2
        q_norm = math.sqrt(q_norm) or 1.0
        for term in q_vec:
            q_vec[term] /= q_norm

        scores = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            policy = self.policies[idx]
            
            # Country & category bonuses
            bonus = 0.0
            if country_filter and policy.get("Country", "").strip().lower() == country_filter.strip().lower():
                bonus += 0.4
            if category_filter and policy.get("Category", "").strip().lower() == category_filter.strip().lower():
                bonus += 0.3

            # Cosine similarity
            dot = sum(q_vec[term] * doc_vec[term] for term in q_vec if term in doc_vec)
            final_score = dot + bonus
            scores.append((final_score, policy))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                **item[1],
                "relevance_score": round(float(item[0]), 3),
                "formatted_doc": f"Country: {item[1].get('Country')}\nCategory: {item[1].get('Category')}\nPolicy: {item[1].get('Policy_Summary')}\nCompliance: {item[1].get('Compliance_Note')}"
            }
            for item in scores[:top_k]
        ]

RETRIEVER = PolicyRetriever(TRADE_POLICIES)

# --- Multi-Agent Implementation ---

def input_agent(product_name, destination, price, quantity, shipping, source_country="United States"):
    t0 = time.time()
    try:
        price = float(price)
        quantity = int(quantity)
        shipping = float(shipping)
    except (ValueError, TypeError):
        raise ValueError("Price, quantity, and shipping must be valid numbers.")

    if not product_name or not destination:
        raise ValueError("Product name and destination country are required.")

    return {
        "product_name": product_name.strip(),
        "source_country": (source_country or "United States").strip(),
        "destination": destination.strip(),
        "price": price,
        "quantity": quantity,
        "shipping": shipping,
        "agent_name": "InputAgent",
        "latency_ms": round((time.time() - t0) * 1000, 2),
        "status": "VALIDATED"
    }

def product_agent(data):
    t0 = time.time()
    query = data["product_name"].lower()
    
    # Match against catalog
    matched = None
    # 1. Exact or starts-with
    for p in PRODUCTS:
        p_name = p.get("Product", "").lower()
        if p_name == query or p_name.startswith(query):
            matched = p
            break
            
    # 2. Substring match
    if not matched:
        for p in PRODUCTS:
            if query in p.get("Product", "").lower():
                matched = p
                break
                
    # 3. Token overlap match
    if not matched:
        q_tokens = set(tokenize(query))
        best_overlap = 0
        for p in PRODUCTS:
            p_tokens = set(tokenize(p.get("Product", "")))
            overlap = len(q_tokens & p_tokens)
            if overlap > best_overlap:
                best_overlap = overlap
                matched = p

    # Fallback default if not found
    if not matched:
        matched = {
            "Product": data["product_name"].title(),
            "HS_Code": "8471.30",
            "Category": "Electronics",
            "Unit": "Piece"
        }

    data["product"] = matched.get("Product")
    data["hs_code"] = matched.get("HS_Code")
    data["category"] = matched.get("Category")
    data["unit"] = matched.get("Unit", "Unit")
    data["product_latency_ms"] = round((time.time() - t0) * 1000, 2)
    return data

def rag_policy_agent(data):
    t0 = time.time()
    query = f"{data['destination']} {data['category']} import policy and compliance requirements"
    
    retrieved = RETRIEVER.retrieve(
        query=query,
        top_k=3,
        country_filter=data["destination"],
        category_filter=data["category"]
    )
    
    top_policy = retrieved[0] if retrieved else None
    
    if top_policy:
        data["policy"] = top_policy.get("Policy_Summary", "Standard commercial tariff applied.")
        data["compliance"] = top_policy.get("Compliance_Note", "Standard customs clearance.")
        data["rag_policy_doc"] = top_policy.get("formatted_doc", "")
        data["source_type"] = top_policy.get("Source_Type", "National Customs Service")
        data["retrieved_policies"] = retrieved
        
        # Determine compliance risk flag
        note = (top_policy.get("Compliance_Note", "") + " " + top_policy.get("Policy_Summary", "")).lower()
        if any(term in note for term in ["prohibited", "banned", "embargo", "sanction"]):
            data["risk_level"] = "CRITICAL_PROHIBITED"
            data["risk_verdict"] = "Import Prohibited / Sanctioned"
        elif any(term in note for term in ["license", "certificate", "bis", "ce mark", "fda", "permit", "inspection"]):
            data["risk_level"] = "REQUIRES_PERMIT"
            data["risk_verdict"] = "Conditional Clearance: Regulatory Certifications Required"
        else:
            data["risk_level"] = "STANDARD_CLEARANCE"
            data["risk_verdict"] = "Cleared: Standard Compliance"
    else:
        data["policy"] = "No specific trade barrier found. Standard WTO MFN rates apply."
        data["compliance"] = "Comply with standard commercial invoice requirements."
        data["rag_policy_doc"] = "Standard WTO MFN regulatory provisions."
        data["source_type"] = "WTO General Tariff Schedule"
        data["risk_level"] = "STANDARD_CLEARANCE"
        data["risk_verdict"] = "Cleared: Standard Compliance"
        data["retrieved_policies"] = []

    data["rag_latency_ms"] = round((time.time() - t0) * 1000, 2)
    return data

def tax_agent(data):
    t0 = time.time()
    dest = data["destination"].lower()
    
    matched_tax = None
    for t in TAXES:
        if t.get("Country", "").lower() == dest:
            matched_tax = t
            break
            
    if not matched_tax:
        # Check partial match
        for t in TAXES:
            if dest in t.get("Country", "").lower() or t.get("Country", "").lower() in dest:
                matched_tax = t
                break

    if not matched_tax:
        # Fallback default
        matched_tax = {
            "Country": data["destination"].title(),
            "Currency": "USD",
            "Default_Import_Duty_Percent": 5.0,
            "GST_VAT_Percent": 10.0
        }

    data["currency"] = matched_tax.get("Currency", "USD")
    data["duty_rate"] = float(matched_tax.get("Default_Import_Duty_Percent", 5.0))
    data["gst_rate"] = float(matched_tax.get("GST_VAT_Percent", 10.0))
    data["matched_country"] = matched_tax.get("Country")
    data["tax_latency_ms"] = round((time.time() - t0) * 1000, 2)
    return data

def calculation_agent(data):
    t0 = time.time()
    product_cost = data["price"] * data["quantity"]
    customs_value = product_cost + data["shipping"]
    customs_duty = customs_value * data["duty_rate"] / 100.0
    taxable_value = customs_value + customs_duty
    gst_vat = taxable_value * data["gst_rate"] / 100.0
    landing_cost = taxable_value + gst_vat
    
    # Financial ratios
    effective_tax_rate = ((customs_duty + gst_vat) / (customs_value or 1.0)) * 100.0
    tax_burden_per_unit = (customs_duty + gst_vat) / (data["quantity"] or 1)
    landed_cost_per_unit = landing_cost / (data["quantity"] or 1)

    # Local currency conversion
    rate = EXCHANGE_RATES.get(data["currency"], 1.0)
    local_landing_cost = landing_cost * rate

    data["product_cost"] = round(product_cost, 2)
    data["customs_value"] = round(customs_value, 2)
    data["customs_duty"] = round(customs_duty, 2)
    data["taxable_value"] = round(taxable_value, 2)
    data["gst_vat"] = round(gst_vat, 2)
    data["landing_cost"] = round(landing_cost, 2)
    data["effective_tax_rate"] = round(effective_tax_rate, 2)
    data["tax_burden_per_unit"] = round(tax_burden_per_unit, 2)
    data["landed_cost_per_unit"] = round(landed_cost_per_unit, 2)
    data["exchange_rate"] = rate
    data["local_landing_cost"] = round(local_landing_cost, 2)
    data["calc_latency_ms"] = round((time.time() - t0) * 1000, 2)
    return data

def report_agent(data):
    t0 = time.time()
    
    # Agent execution steps log
    steps = [
        {
            "step": 1,
            "agent": "Input Agent",
            "status": "COMPLETED",
            "latency": f"{data.get('latency_ms', 0)} ms",
            "description": f"Sanitized payload: {data['quantity']}x {data['product_name']} @ ${data['price']} | {data.get('source_country', 'Origin')} -> {data['destination']}"
        },
        {
            "step": 2,
            "agent": "Product Agent",
            "status": "COMPLETED",
            "latency": f"{data.get('product_latency_ms', 0)} ms",
            "description": f"Catalog mapped to '{data['product']}', HS Code: {data['hs_code']}, Category: {data['category']}"
        },
        {
            "step": 3,
            "agent": "RAG Policy Agent",
            "status": "COMPLETED",
            "latency": f"{data.get('rag_latency_ms', 0)} ms",
            "description": f"Retrieved regulatory policy: {data.get('risk_verdict')}"
        },
        {
            "step": 4,
            "agent": "Tax Agent",
            "status": "COMPLETED",
            "latency": f"{data.get('tax_latency_ms', 0)} ms",
            "description": f"Applied {data['destination']} tariff schedule: Duty {data['duty_rate']}%, GST/VAT {data['gst_rate']}% ({data['currency']})"
        },
        {
            "step": 5,
            "agent": "Calculation Agent",
            "status": "COMPLETED",
            "latency": f"{data.get('calc_latency_ms', 0)} ms",
            "description": f"Landed cost: ${data['landing_cost']:.2f} ({data['currency']} {data['local_landing_cost']:,.2f})"
        },
        {
            "step": 6,
            "agent": "Report Agent",
            "status": "COMPLETED",
            "latency": f"{round((time.time() - t0) * 1000, 2)} ms",
            "description": "Consolidated full audit provenance trace and executive risk assessment."
        }
    ]

    data["execution_steps"] = steps
    data["total_pipeline_latency_ms"] = round(
        data.get("latency_ms", 0) +
        data.get("product_latency_ms", 0) +
        data.get("rag_latency_ms", 0) +
        data.get("tax_latency_ms", 0) +
        data.get("calc_latency_ms", 0) +
        (time.time() - t0) * 1000,
        2
    )
    data["audit_id"] = f"AUD-{int(time.time()*1000)%1000000:06d}"
    data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    return data

def run_agentic_auditor_pipeline(product_name, destination, price, quantity, shipping, source_country="United States"):
    data = input_agent(product_name, destination, price, quantity, shipping, source_country)
    data = product_agent(data)
    data = rag_policy_agent(data)
    data = tax_agent(data)
    data = calculation_agent(data)
    data = report_agent(data)
    return data

def run_normal_auditor_pipeline(product_name, destination, price, quantity, shipping, source_country="United States"):
    """Replicates normal rule-based auditor from Cell 55 of notebook"""
    t0 = time.time()
    try:
        price = float(price)
        quantity = int(quantity)
        shipping = float(shipping)
    except:
        return {"error": "Invalid numeric inputs"}

    # Basic product contains
    matched_prod = None
    for p in PRODUCTS:
        if product_name.lower() in p.get("Product", "").lower():
            matched_prod = p
            break
    if not matched_prod:
        matched_prod = {"Product": product_name, "HS_Code": "N/A", "Category": "General"}

    # Basic tax match
    matched_tax = None
    for t in TAXES:
        if t.get("Country", "").lower() == destination.lower():
            matched_tax = t
            break
    if not matched_tax:
        matched_tax = {"Country": destination, "Default_Import_Duty_Percent": 5.0, "GST_VAT_Percent": 10.0, "Currency": "USD"}

    product_cost = price * quantity
    customs_value = product_cost + shipping
    duty = customs_value * float(matched_tax["Default_Import_Duty_Percent"]) / 100.0
    taxable_value = customs_value + duty
    gst = taxable_value * float(matched_tax["GST_VAT_Percent"]) / 100.0
    landing_cost = taxable_value + gst

    return {
        "product": matched_prod.get("Product"),
        "hs_code": matched_prod.get("HS_Code"),
        "source_country": source_country,
        "destination": matched_tax.get("Country"),
        "import_duty_rate": matched_tax["Default_Import_Duty_Percent"],
        "gst_vat_rate": matched_tax["GST_VAT_Percent"],
        "product_cost": round(product_cost, 2),
        "customs_value": round(customs_value, 2),
        "customs_duty": round(duty, 2),
        "gst_vat": round(gst, 2),
        "landing_cost": round(landing_cost, 2),
        "latency_ms": round((time.time() - t0) * 1000, 2),
        "policy": "No automated policy verification (Normal System)",
        "compliance": "Not checked in standard calculator",
        "rag_available": False,
        "specialized_agents": False
    }

# --- API Endpoints ---

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "AI Tax Auditor Backend",
        "products_count": len(PRODUCTS),
        "countries_count": len(TAXES),
        "policies_count": len(TRADE_POLICIES),
        "transactions_count": len(SAMPLE_TRANSACTIONS)
    })

@app.route("/api/audit/agentic", methods=["POST"])
def audit_agentic():
    req = request.get_json(force=True)
    product_name = req.get("product_name", "")
    destination = req.get("destination", "")
    source_country = req.get("source_country", req.get("origin", "United States"))
    price = req.get("price", 0)
    quantity = req.get("quantity", 1)
    shipping = req.get("shipping", 0)

    try:
        result = run_agentic_auditor_pipeline(product_name, destination, price, quantity, shipping, source_country)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/audit/normal", methods=["POST"])
def audit_normal():
    req = request.get_json(force=True)
    product_name = req.get("product_name", "")
    destination = req.get("destination", "")
    price = req.get("price", 0)
    quantity = req.get("quantity", 1)
    shipping = req.get("shipping", 0)

    try:
        result = run_normal_auditor_pipeline(product_name, destination, price, quantity, shipping)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/audit/compare", methods=["POST"])
def audit_compare():
    req = request.get_json(force=True)
    product_name = req.get("product_name", "")
    destination = req.get("destination", "")
    price = req.get("price", 0)
    quantity = req.get("quantity", 1)
    shipping = req.get("shipping", 0)

    try:
        agentic_res = run_agentic_auditor_pipeline(product_name, destination, price, quantity, shipping)
        normal_res = run_normal_auditor_pipeline(product_name, destination, price, quantity, shipping)
        
        comparison = {
            "features": [
                {"feature": "Product Identification", "normal": True, "agentic": True},
                {"feature": "Tax Calculation", "normal": True, "agentic": True},
                {"feature": "Policy Lookup", "normal": True, "agentic": True},
                {"feature": "Specialized Agents", "normal": False, "agentic": True},
                {"feature": "Semantic Search", "normal": False, "agentic": True},
                {"feature": "RAG Regulatory Evidence", "normal": False, "agentic": True},
                {"feature": "Compliance Risk Assessment", "normal": False, "agentic": True},
                {"feature": "Agent Provenance Trace", "normal": False, "agentic": True}
            ],
            "agentic": agentic_res,
            "normal": normal_res,
            "cost_difference": round(agentic_res["landing_cost"] - normal_res["landing_cost"], 2)
        }
        return jsonify({"success": True, "data": comparison})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    search = request.args.get("search", "").lower()
    filter_risk = request.args.get("risk", "")

    results = []
    for tx in SAMPLE_TRANSACTIONS:
        prod = tx.get("Product", "")
        origin = tx.get("Origin_Country", "")
        dest = tx.get("Destination_Country", "")
        hs = tx.get("HS_Code", "")

        if search:
            match = (
                search in prod.lower() or
                search in origin.lower() or
                search in dest.lower() or
                search in hs.lower()
            )
            if not match:
                continue

        # Quick simulated tax computation for each transaction
        price = float(tx.get("Unit_Price_USD", 0))
        qty = int(tx.get("Quantity", 1))
        shipping = float(tx.get("Shipping_USD", 0))
        
        # Match tax
        tax_rate = 10.0
        gst_rate = 12.0
        for t in TAXES:
            if t.get("Country", "").lower() == dest.lower():
                tax_rate = float(t.get("Default_Import_Duty_Percent", 10.0))
                gst_rate = float(t.get("GST_VAT_Percent", 12.0))
                break

        product_cost = price * qty
        customs_val = product_cost + shipping
        duty = customs_val * tax_rate / 100.0
        taxable = customs_val + duty
        vat = taxable * gst_rate / 100.0
        landing = taxable + vat

        # Identify potential compliance flags
        has_flag = False
        flag_reason = "Standard Clear"
        if duty > 5000:
            has_flag = True
            flag_reason = "High Customs Value Inspection"
        elif tax_rate >= 15:
            has_flag = True
            flag_reason = "Elevated Tariff Barrier"

        item = {
            **tx,
            "Product_Cost_USD": round(product_cost, 2),
            "Customs_Value_USD": round(customs_val, 2),
            "Duty_USD": round(duty, 2),
            "Duty_Rate_Percent": tax_rate,
            "GST_VAT_USD": round(vat, 2),
            "Landing_Cost_USD": round(landing, 2),
            "Audit_Status": "FLAGGED" if has_flag else "CLEARED",
            "Audit_Reason": flag_reason
        }

        if filter_risk == "FLAGGED" and not has_flag:
            continue
        if filter_risk == "CLEARED" and has_flag:
            continue

        results.append(item)

    paginated = results[offset:offset + limit]
    return jsonify({
        "total": len(results),
        "total_unfiltered": len(SAMPLE_TRANSACTIONS),
        "limit": limit,
        "offset": offset,
        "items": paginated
    })

@app.route("/api/policies", methods=["GET"])
def get_policies():
    query = request.args.get("query", "")
    country = request.args.get("country", "")
    category = request.args.get("category", "")
    limit = int(request.args.get("limit", 50))

    if query:
        results = RETRIEVER.retrieve(query, top_k=limit, country_filter=country, category_filter=category)
    else:
        filtered = []
        for p in TRADE_POLICIES:
            if country and p.get("Country", "").lower() != country.lower():
                continue
            if category and p.get("Category", "").lower() != category.lower():
                continue
            filtered.append(p)
        results = filtered[:limit]

    return jsonify({
        "total": len(results),
        "items": results
    })

@app.route("/api/products", methods=["GET"])
def get_products():
    query = request.args.get("query", "").lower()
    limit = int(request.args.get("limit", 20))
    
    if not query:
        return jsonify({"items": PRODUCTS[:limit]})
        
    matched = []
    for p in PRODUCTS:
        if query in p.get("Product", "").lower() or query in p.get("HS_Code", "").lower():
            matched.append(p)
            if len(matched) >= limit:
                break
    return jsonify({"items": matched})

@app.route("/api/countries", methods=["GET"])
def get_countries():
    return jsonify({
        "countries": TAXES
    })

@app.route("/api/stats", methods=["GET"])
def get_stats():
    total_tx_val = sum(float(t.get("Unit_Price_USD", 0)) * int(t.get("Quantity", 1)) for t in SAMPLE_TRANSACTIONS)
    total_shipping = sum(float(t.get("Shipping_USD", 0)) for t in SAMPLE_TRANSACTIONS)
    avg_duty = sum(float(t.get("Default_Import_Duty_Percent", 0)) for t in TAXES) / (len(TAXES) or 1)
    avg_vat = sum(float(t.get("GST_VAT_Percent", 0)) for t in TAXES) / (len(TAXES) or 1)

    return jsonify({
        "total_products": len(PRODUCTS),
        "total_countries": len(TAXES),
        "total_policies": len(TRADE_POLICIES),
        "total_sample_transactions": len(SAMPLE_TRANSACTIONS),
        "total_transaction_value_usd": round(total_tx_val, 2),
        "total_shipping_usd": round(total_shipping, 2),
        "average_duty_percent": round(avg_duty, 2),
        "average_vat_percent": round(avg_vat, 2)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting AI Tax Auditor Backend on http://127.0.0.1:{port}...")
    app.run(host="0.0.0.0", port=port, debug=False)

const BASE_URL = "http://127.0.0.1:8000";
let accessToken = localStorage.getItem("bizsafi_token") || "";

const output = document.getElementById("output");
const businessList = document.getElementById("business-list");
const authState = document.getElementById("auth-state");
document.getElementById("api-base").textContent = BASE_URL;

function val(id) {
  return document.getElementById(id).value.trim();
}

function print(data) {
  output.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

function setAuthState() {
  authState.textContent = accessToken ? "Authenticated" : "Not authenticated";
}

function setToken(token) {
  accessToken = token || "";
  if (accessToken) {
    localStorage.setItem("bizsafi_token", accessToken);
  } else {
    localStorage.removeItem("bizsafi_token");
  }
  setAuthState();
}

async function api(path, method = "GET", body = null, auth = false) {
  const headers = { "Content-Type": "application/json" };
  if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });
  const text = await res.text();
  const payload = (() => {
    try { return JSON.parse(text); } catch { return text; }
  })();
  if (!res.ok) throw new Error(JSON.stringify(payload));
  return payload;
}

function renderBusinesses(items) {
  if (!items.length) {
    businessList.innerHTML = "<div class='list-item'>No businesses yet.</div>";
    return;
  }
  businessList.innerHTML = items.map((biz) => (
    `<div class="list-item" data-id="${biz.id}">
      <span><strong>${biz.name}</strong> (${biz.category})<br/><small>${biz.location || "No location"}</small></span>
      <span>#${biz.id}</span>
    </div>`
  )).join("");

  businessList.querySelectorAll(".list-item[data-id]").forEach((item) => {
    item.addEventListener("click", () => {
      document.getElementById("business-id").value = item.getAttribute("data-id");
    });
  });
}

document.getElementById("register-btn").onclick = async () => {
  try {
    const payload = await api("/auth/register", "POST", {
      name: val("name"),
      email: val("email"),
      password: val("password"),
    });
    print(payload);
  } catch (e) { print(e.message); }
};

document.getElementById("login-btn").onclick = async () => {
  try {
    const payload = await api("/auth/login", "POST", {
      email: val("email"),
      password: val("password"),
    });
    setToken(payload.access_token);
    print({ message: "Login successful", token: accessToken, user: payload.user });
    const businesses = await api("/business/", "GET", null, true);
    renderBusinesses(businesses);
  } catch (e) { print(e.message); }
};

document.getElementById("me-btn").onclick = async () => {
  try { print(await api("/auth/me", "GET", null, true)); }
  catch (e) { print(e.message); }
};

document.getElementById("create-business-btn").onclick = async () => {
  try {
    const biz = await api("/business/", "POST", {
      name: val("biz-name"),
      category: val("biz-category"),
      location: val("biz-location"),
    }, true);
    document.getElementById("business-id").value = biz.id;
    print(biz);
    const businesses = await api("/business/", "GET", null, true);
    renderBusinesses(businesses);
  } catch (e) { print(e.message); }
};

document.getElementById("list-business-btn").onclick = async () => {
  try {
    const businesses = await api("/business/", "GET", null, true);
    renderBusinesses(businesses);
    print(businesses);
  }
  catch (e) { print(e.message); }
};

document.getElementById("add-sale-btn").onclick = async () => {
  try {
    print(await api("/sales/", "POST", {
      business_id: Number(val("business-id")),
      amount: Number(val("sale-amount")),
      notes: "Sale from frontend starter",
    }, true));
  } catch (e) { print(e.message); }
};

document.getElementById("add-stock-btn").onclick = async () => {
  try {
    print(await api("/stock/", "POST", {
      business_id: Number(val("business-id")),
      item_name: val("stock-item"),
      quantity: 20,
      cost_price: 180,
      selling_price: 250,
      low_stock_threshold: 5,
    }, true));
  } catch (e) { print(e.message); }
};

document.getElementById("add-reminder-btn").onclick = async () => {
  try {
    const due = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    print(await api("/reminders/", "POST", {
      business_id: Number(val("business-id")),
      type: "permit",
      message: "Permit renewal reminder",
      due_date: due,
    }, true));
  } catch (e) { print(e.message); }
};

document.getElementById("summary-btn").onclick = async () => {
  try {
    const id = Number(val("business-id"));
    print(await api(`/sales/summary?business_id=${id}&period=today`, "GET", null, true));
  } catch (e) { print(e.message); }
};

document.getElementById("logout-btn").onclick = () => {
  setToken("");
  print("Logged out.");
};

setAuthState();

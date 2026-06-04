const colorLabels = {
  red: "Đỏ",
  yellow: "Vàng",
  blue: "Xanh dương"
};

let chart;

function initChart() {
  const canvas = document.getElementById("colorChart");
  if (!canvas) return;
  chart = new Chart(canvas, {
    type: "doughnut",
    data: { labels: [], datasets: [{ data: [], backgroundColor: [], borderWidth: 0 }] },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#cbd5e1", usePointStyle: true } } },
      cutout: "62%"
    }
  });
}

async function refreshStats() {
  const res = await fetch("/api/stats");
  const data = await res.json();
  const realtime = data.realtime || {};

  setText("totalObjects", realtime.total_objects ?? 0);
  setText("fpsCounter", realtime.fps ?? "0.0");
  setText("defectCount", data.defects ?? 0);
  setText("modelStatus", realtime.model_status || "Unknown");
  setText("targetColorText", realtime.target_color ? colorLabels[realtime.target_color] : "None");
  updateBlockchain(data.blockchain || {});
  updateRobotSimulator(realtime.events || [], realtime.robot_serial || {});

  updateCounters(data.stats || []);
  updateChart(data.stats || []);
  updateLogs(realtime.events || []);
  refreshBlockchainRecords();
  if ((realtime.events || []).some((item) => item.status === "wrong_color" || item.status === "NG")) showToast();
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function updateCounters(stats) {
  const wrap = document.getElementById("colorCounters");
  if (!wrap) return;
  wrap.innerHTML = stats.map((item) => `
    <div class="color-row">
      <span class="swatch" style="background:${item.hex}"></span>
      <span>${item.label}</span>
      <strong>${item.count}</strong>
    </div>
  `).join("");
}

function updateChart(stats) {
  if (!chart) return;
  const targetStats = stats.filter((item) => ["red", "yellow", "blue"].includes(item.color));
  chart.data.labels = targetStats.map((item) => item.label);
  chart.data.datasets[0].data = targetStats.map((item) => item.count);
  chart.data.datasets[0].backgroundColor = targetStats.map((item) => item.hex);
  chart.update("none");
}

function updateRobotSimulator(events, serialStatus = {}) {
  const modeBadge = document.getElementById("robotModeBadge");
  if (modeBadge) {
    const serialEnabled = Boolean(serialStatus.enabled);
    const status = serialStatus.status || (serialEnabled ? "starting" : "SIM");
    modeBadge.textContent = serialEnabled ? status.toUpperCase() : "SIM";
    modeBadge.classList.toggle("ok", serialEnabled && ["connected", "sent"].some((item) => status.includes(item)));
    modeBadge.classList.toggle("ng", serialEnabled && status.includes("error"));
    modeBadge.classList.toggle("ignored", !serialEnabled || (!status.includes("error") && !status.includes("connected") && status !== "sent"));
  }

  const active = events.find((event) => event.robot?.enabled) || events[0];
  if (!active) {
    setText("robotCommandText", "WAIT");
    setText("robotCenter", "-");
    setText("robotPickPosition", "-");
    setText("robotDropBin", "-");
    setText("robotLastCommand", "WAIT");
    return;
  }

  const robot = active.robot || {};
  const serial = active.robot_serial || serialStatus || {};
  const pick = robot.pick_position || {};
  const commandText = serial.sent ? `SENT: ${serial.command}` : (robot.command || serial.command || "WAIT");
  setText("robotCommandText", commandText);
  setText("robotCenter", active.center_text || robot.center_text || "-");
  setText("robotPickPosition", formatPosition(pick));
  setText("robotDropBin", robot.target_bin_label || "-");
  setText("robotLastCommand", commandText);
}

function formatPosition(position) {
  if (!position || position.x === undefined) return "-";
  return `X:${position.x} Y:${position.y} Z:${position.z}`;
}

function updateLogs(events) {
  const body = document.getElementById("logTable");
  if (!body) return;
  const now = new Date().toLocaleTimeString("vi-VN");
  body.innerHTML = events.map((event) => `
    <tr>
      <td>${now}</td>
      <td>${event.object_name}</td>
      <td><span class="mini-dot" style="background:${event.hex}"></span>${event.detected_color_label}</td>
      <td>
        <span class="mini-dot" style="background:${event.detected_hex || event.hex}"></span>${event.detected_hex || ""}
        <div class="cell-muted">${Array.isArray(event.detected_rgb) ? event.detected_rgb.join(",") : event.rgb_value}</div>
      </td>
      <td>
        ${event.standard_hex || "-"}
        <div class="cell-muted">${Array.isArray(event.standard_rgb) ? event.standard_rgb.join(",") : "-"}</div>
      </td>
      <td>${event.color_distance ?? "-"}</td>
      <td><span class="status-badge ${event.match_standard ? "ok" : "ng"}">${event.match_standard ? "true" : "false"}</span></td>
      <td>${event.rgb_value}</td>
      <td>${event.hsv_value}</td>
      <td>${event.center_text || "-"}</td>
      <td>
        <span class="status-badge ${event.robot?.enabled ? "ok" : "ignored"}">${event.robot_command || "WAIT"}</span>
        <div class="cell-muted">${event.robot?.target_bin_label || "-"}</div>
      </td>
      <td>${Number(event.confidence).toFixed(2)}</td>
      <td><span class="status-badge ${statusClass(event.status)}">${event.status}</span></td>
      <td><span class="cell-muted">${shortHash(event.result_hash)}</span></td>
      <td><span class="status-badge ${event.status === "ignored" ? "ignored" : "ng"}">${event.status === "ignored" ? "skipped" : "queued"}</span></td>
    </tr>
  `).join("");
}

function shortHash(hash) {
  return hash ? `${hash.slice(0, 10)}...${hash.slice(-6)}` : "-";
}

function statusClass(status) {
  if (status === "valid" || status === "OK") return "ok";
  if (status === "ignored") return "ignored";
  return "ng";
}

function updateBlockchain(blockchain) {
  const hasContract = Boolean(document.getElementById("contractAddress")?.value.trim());
  setText("blockchainStatus", blockchain.ready ? "Ket noi thanh cong" : (hasContract ? (blockchain.status || "Chua ket noi") : "Chua ket noi"));
  setChainRecordCount(blockchain);
  setText("lastTxHash", blockchain.last_tx_hash || "None");
  const badge = document.getElementById("blockchainReadyBadge");
  if (badge) {
    badge.textContent = blockchain.ready ? "CONNECTED" : "OFFLINE";
    badge.classList.toggle("ok", Boolean(blockchain.ready));
    badge.classList.toggle("ng", !blockchain.ready);
  }
  const provider = document.getElementById("providerUri");
  if (provider && blockchain.provider_uri && document.activeElement !== provider) {
    provider.value = blockchain.provider_uri;
  }
  const contract = document.getElementById("contractAddress");
  if (contract && blockchain.contract_address && document.activeElement !== contract) {
    contract.value = blockchain.contract_address;
  }
  const account = document.getElementById("accountAddress");
  if (account && blockchain.account_address && document.activeElement !== account) {
    account.value = blockchain.account_address;
  }
  const chainId = document.getElementById("chainId");
  if (chainId && blockchain.chain_id && document.activeElement !== chainId) {
    chainId.value = blockchain.chain_id;
  }
}

function setChainRecordCount(blockchain = {}) {
  const total = blockchain.total_records ?? blockchain.totalRecords ?? blockchain.records_on_chain;
  if (total !== null && total !== undefined) {
    setText("chainRecordCount", Number(total));
  }
}

async function refreshBlockchainRecords() {
  try {
    const res = await fetch("/api/blockchain/records");
    const data = await res.json();
    setChainRecordCount(data);
    if (data.blockchain) updateBlockchain(data.blockchain);
  } catch {
    // Keep the last visible on-chain count if Ganache is temporarily unavailable.
  }
}

function showToast() {
  const toast = document.getElementById("toastAlert");
  if (!toast) return;
  toast.classList.add("show");
  if ("speechSynthesis" in window) {
    const utterance = new SpeechSynthesisUtterance("Cảnh báo sai màu");
    utterance.lang = "vi-VN";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }
  setTimeout(() => toast.classList.remove("show"), 2400);
}

function bindControls() {
  const target = document.getElementById("targetColor");
  const slider = document.getElementById("confidenceSlider");
  const confidenceValue = document.getElementById("confidenceValue");

  target?.addEventListener("change", async () => {
    await fetch("/set-target-color", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_color: target.value })
    });
  });

  slider?.addEventListener("input", () => {
    confidenceValue.textContent = slider.value;
  });
  slider?.addEventListener("change", async () => {
    await fetch("/set-confidence", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confidence: slider.value })
    });
  });

  bindUpload("imageForm", "/upload-image");
  bindUpload("videoForm", "/upload-video");
  bindCameraSource();
  resetBlockchainForm();
  bindBlockchainConfig();
  bindBlockchainTest();
}

async function bindCameraSource() {
  const button = document.getElementById("applyCameraSource");
  const source = document.getElementById("cameraSource");
  if (!button || !source) return;
  try {
    const res = await fetch("/api/camera/status");
    const data = await res.json();
    if (data.camera?.camera_index !== undefined) source.value = String(data.camera.camera_index);
    updateCameraStatus(data.camera);
  } catch {
    updateCameraStatus({ error: "Khong doc duoc trang thai webcam" });
  }
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "Dang mo...";
    try {
      const res = await fetch("/api/camera/source", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ camera_index: source.value })
      });
      const data = await res.json();
      updateCameraStatus(data.camera, data.message);
      if (data.ok) reloadCameraFeed();
    } finally {
      button.disabled = false;
      button.textContent = "Dung webcam";
    }
  });
}

function updateCameraStatus(camera = {}, message = "") {
  const status = document.getElementById("cameraStatus");
  if (!status) return;
  if (message) {
    status.textContent = message;
  } else if (camera.running) {
    status.textContent = camera.has_frame
      ? `Dang dung Camera ${camera.camera_index}`
      : `Camera ${camera.camera_index} da mo nhung chua co hinh`;
  } else {
    status.textContent = camera.error || "Chua mo webcam";
  }
}

function reloadCameraFeed() {
  const feed = document.getElementById("cameraFeed");
  if (feed) feed.src = `/video_feed?t=${Date.now()}`;
}

function resetBlockchainForm() {
  const contract = document.getElementById("contractAddress");
  const account = document.getElementById("accountAddress");
  const privateKey = document.getElementById("privateKey");
  const chainId = document.getElementById("chainId");
  if (contract) contract.value = contract.value || "";
  if (account) account.value = account.value || "";
  if (privateKey) privateKey.value = "";
  if (chainId) chainId.value = "1337";
  setText("blockchainStatus", "Chua ket noi");
  setText("chainRecordCount", 0);
  setText("lastTxHash", "None");
}

function bindBlockchainConfig() {
  const button = document.getElementById("saveBlockchainConfig");
  if (!button) return;
  button.addEventListener("click", async () => {
    const providerInput = document.getElementById("providerUri");
    const providerUri = normalizeProviderUri(providerInput?.value);
    if (providerInput) providerInput.value = providerUri;
    const contractAddress = document.getElementById("contractAddress")?.value.trim();
    const accountAddress = document.getElementById("accountAddress")?.value.trim();
    const privateKey = document.getElementById("privateKey")?.value.trim();
    const chainId = document.getElementById("chainId")?.value.trim() || "1337";
    if (!/^0x[a-fA-F0-9]{40}$/.test(contractAddress || "")) {
      const message = "Contract address phai la dia chi 0x day du 42 ky tu";
      setText("blockchainStatus", `Loi: ${message}`);
      alert(`Loi blockchain: ${message}`);
      return;
    }
    if (accountAddress && !/^0x[a-fA-F0-9]{40}$/.test(accountAddress)) {
      const message = "Account address phai la dia chi 0x day du 42 ky tu";
      setText("blockchainStatus", `Loi: ${message}`);
      alert(`Loi blockchain: ${message}`);
      return;
    }
    if (privateKey && !/^(0x)?[a-fA-F0-9]{64}$/.test(privateKey)) {
      const message = "Private key phai day du 64 ky tu hex";
      setText("blockchainStatus", `Loi: ${message}`);
      alert(`Loi blockchain: ${message}`);
      return;
    }
    button.disabled = true;
    button.textContent = "Đang kết nối...";
    try {
      const res = await fetch("/api/blockchain/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider_uri: document.getElementById("providerUri")?.value,
          contract_address: contractAddress,
          account_address: accountAddress,
          private_key: privateKey,
          chain_id: chainId
        })
      });
      const data = await res.json();
      updateBlockchain(data.blockchain || {});
      await refreshBlockchainRecords();
      if (data.ok) {
        button.textContent = "Thanh cong";
        setTimeout(() => {
          button.textContent = "Ket noi blockchain";
        }, 1200);
      } else {
        showBlockchainError(blockchainErrorMessage(data));
      }
    } finally {
      button.disabled = false;
      if (button.textContent !== "Thanh cong") {
        button.textContent = "Ket noi blockchain";
      }
    }
  });
}

function normalizeProviderUri(value) {
  let uri = (value || "").trim();
  if (uri.startsWith("http//")) uri = `http://${uri.slice(6)}`;
  if (uri.startsWith("https//")) uri = `https://${uri.slice(7)}`;
  if (uri && !uri.includes("://")) uri = `http://${uri}`;
  return uri || "http://127.0.0.1:7545";
}

function blockchainErrorMessage(data) {
  const blockchain = data.blockchain || {};
  const diagnostics = blockchain.diagnostics || {};
  const status = data.message || blockchain.status || "";
  if (status.includes("Ganache RPC chua mo")) {
    return `${status}. Hay mo Ganache workspace va kiem tra RPC Server dung cong 7545.`;
  }
  if (blockchain.contract_address && diagnostics.rpc_connected && diagnostics.block_number === 0 && !diagnostics.contract_deployed) {
    return "Ganache da ket noi OK, nhung chua co contract nao tren Ganache. Trong Remix hay doi Environment sang Custom/External HTTP Provider: http://127.0.0.1:7545 roi deploy lai.";
  }
  if (blockchain.contract_address && diagnostics.rpc_connected && !diagnostics.contract_deployed) {
    return "Ganache da ket noi OK, nhung contract address khong nam tren Ganache hien tai. Hay copy address sau khi deploy bang Ganache RPC.";
  }
  return data.message || blockchain.status || "Khong ket noi duoc blockchain";
}

function showBlockchainError(message) {
  const cleanMessage = String(message || "Khong ket noi duoc blockchain").replace(/^Loi:\s*/i, "");
  setText("blockchainStatus", `Loi: ${cleanMessage}`);
  alert(`Loi blockchain: ${cleanMessage}`);
}

function bindBlockchainTest() {
  const button = document.getElementById("testBlockchainLog");
  if (!button) return;
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "Đang test...";
    try {
      const res = await fetch("/api/blockchain/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: `TEST-${Date.now()}`,
          object_name: "dashboard-test",
          detected_color: "red",
          status: "valid"
        })
      });
      await res.json();
      await refreshStats();
      await refreshBlockchainRecords();
    } finally {
      button.disabled = false;
      button.textContent = "Test ghi log";
    }
  });
}

function bindUpload(formId, endpoint) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const status = document.getElementById("uploadStatus");
    status.textContent = "Đang xử lý, vui lòng chờ...";
    status.classList.add("loading");
    try {
      const res = await fetch(endpoint, { method: "POST", body: new FormData(form) });
      const data = await res.json();
      status.classList.remove("loading");
      status.innerHTML = data.ok
        ? `${data.message} ${data.result?.output_url ? `<a href="${data.result.output_url}" target="_blank">Xem kết quả</a>` : ""}`
        : data.message;
    } catch (err) {
      status.classList.remove("loading");
      status.textContent = "Có lỗi khi upload hoặc xử lý file.";
    }
  });
}

initChart();
bindControls();
refreshStats();
setInterval(refreshStats, 1200);

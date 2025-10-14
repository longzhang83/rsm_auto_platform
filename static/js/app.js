const form = document.getElementById("voucher-form");
const statusEl = document.getElementById("status");

function setStatus(message, type = "info") {
	if (!statusEl) return;
	const colorMap = {
		info: "text-slate-600",
		success: "text-emerald-600",
		error: "text-rose-600",
	};
	statusEl.className = `text-sm ${colorMap[type] ?? colorMap.info}`;
	statusEl.textContent = message;
}

function parseFilename(disposition) {
	if (!disposition) return null;
	const match = disposition.match(/filename="?([^";]+)"?/i);
	return match ? decodeURIComponent(match[1]) : null;
}

async function submitForm(event) {
	event.preventDefault();
	setStatus("正在生成凭证...", "info");

	const submitButton = form.querySelector("button[type='submit']");
	if (submitButton) {
		submitButton.disabled = true;
		submitButton.classList.add("opacity-80");
	}

	const formData = new FormData(form);

	try {
		const response = await fetch("/api/generate", {
			method: "POST",
			body: formData,
		});

		if (!response.ok) {
			let detail = "生成失败，请检查输入数据。";
			try {
				const payload = await response.json();
				if (payload?.detail) {
					detail = Array.isArray(payload.detail)
						? payload.detail.map((item) => item.msg ?? item).join("；")
						: payload.detail;
				}
			} catch (_) {
				// ignore
			}
			throw new Error(detail);
		}

		const blob = await response.blob();
		const filename =
			parseFilename(response.headers.get("content-disposition")) || "vouchers_bundle.zip";

		const url = window.URL.createObjectURL(blob);
		const link = document.createElement("a");
		link.href = url;
		link.download = filename;
		document.body.appendChild(link);
		link.click();
		link.remove();
		window.URL.revokeObjectURL(url);

		setStatus("凭证生成完成，文件已开始下载。", "success");
	} catch (error) {
		setStatus(error.message || "生成失败，请稍后再试。", "error");
	} finally {
		if (submitButton) {
			submitButton.disabled = false;
			submitButton.classList.remove("opacity-80");
		}
	}
}

if (form) {
	form.addEventListener("submit", submitForm);
}

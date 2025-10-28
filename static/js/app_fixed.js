// 选项卡功能
function initTabs() {
	const tabButtons = document.querySelectorAll('.tab-button');
	const tabPanels = document.querySelectorAll('.tab-panel');

	tabButtons.forEach(button => {
		button.addEventListener('click', () => {
			const targetTab = button.getAttribute('data-tab');

			// 更新按钮状态
			tabButtons.forEach(btn => {
				if (btn.getAttribute('data-tab') === targetTab) {
					btn.classList.add('border-sky-500', 'text-sky-600');
					btn.classList.remove('border-transparent', 'text-gray-500', 'hover:text-gray-700', 'hover:border-gray-300');
				} else {
					btn.classList.remove('border-sky-500', 'text-sky-600');
					btn.classList.add('border-transparent', 'text-gray-500', 'hover:text-gray-700', 'hover:border-gray-300');
				}
			});

			// 更新面板显示
			tabPanels.forEach(panel => {
				if (panel.id === `${targetTab}-panel`) {
					panel.classList.remove('hidden');
				} else {
					panel.classList.add('hidden');
				}
			});
		});
	});
}

// 状态管理
function setStatus(elementId, message, type = "info") {
	const statusEl = document.getElementById(elementId);
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

// 通用表单提交处理
async function submitForm(form, endpoint, successMessage, statusElementId) {
	const statusEl = document.getElementById(statusElementId);
	const submitButton = form.querySelector("button[type='submit']");

	// 设置状态
	setStatus(statusElementId, "处理中...", "info");

	if (submitButton) {
		submitButton.disabled = true;
		submitButton.classList.add("opacity-80");
	}

	const formData = new FormData(form);

	// 调试信息
	console.log(`提交表单到 ${endpoint}`);
	console.log('FormData 内容:');
	for (let [key, value] of formData.entries()) {
		console.log(`  ${key}:`, value instanceof File ? `File(${value.name})` : value);
	}

	try {
		const response = await fetch(endpoint, {
			method: "POST",
			body: formData,
		});

		console.log(`响应状态: ${response.status}`);

		if (!response.ok) {
			let detail = "处理失败，请检查输入数据。";
			try {
				const payload = await response.json();
				console.log('错误响应:', payload);
				if (payload?.detail) {
					detail = Array.isArray(payload.detail)
						? payload.detail.map((item) => item.msg ?? item).join("；")
						: payload.detail;
				}
			} catch (_) {
				console.log('无法解析错误响应为JSON');
			}
			throw new Error(detail);
		}

		const blob = await response.blob();
		const filename = parseFilename(response.headers.get("content-disposition")) || "output.zip";

		console.log(`下载文件: ${filename}`);

		// 下载文件
		const url = window.URL.createObjectURL(blob);
		const link = document.createElement("a");
		link.href = url;
		link.download = filename;
		document.body.appendChild(link);
		link.click();
		link.remove();
		window.URL.revokeObjectURL(url);

		setStatus(statusElementId, successMessage, "success");
	} catch (error) {
		console.error('请求失败:', error);
		setStatus(statusElementId, error.message || "处理失败，请稍后再试。", "error");
	} finally {
		if (submitButton) {
			submitButton.disabled = false;
			submitButton.classList.remove("opacity-80");
		}
	}
}

// 凭证生成表单处理
async function submitVoucherForm(event) {
	event.preventDefault();
	const form = event.target;

	console.log('凭证生成表单提交');

	await submitForm(
		form,
		"/api/generate",
		"凭证生成完成，文件已开始下载。",
		"voucher-status"
	);
}

// 摘要翻译表单处理
async function submitTranslateForm(event) {
	event.preventDefault();
	const form = event.target;

	console.log('摘要翻译表单提交');

	// 处理复选框值 - 只有选中时才包含在FormData中
	const formData = new FormData(form);
	const forceCheckbox = form.querySelector('input[name="force"]');
	if (forceCheckbox && !forceCheckbox.checked) {
		// 如果复选框未选中，完全移除该字段
		formData.delete('force');
		console.log('复选框未选中，移除force字段');
	} else if (forceCheckbox && forceCheckbox.checked) {
		console.log('复选框已选中，包含force字段');
	}

	await submitForm(
		form,
		"/api/translate",
		"摘要翻译完成，文件已开始下载。",
		"translate-status"
	);
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
	console.log('应用初始化开始');

	// 初始化选项卡
	initTabs();
	console.log('选项卡初始化完成');

	// 绑定凭证生成表单
	const voucherForm = document.getElementById("voucher-form");
	if (voucherForm) {
		voucherForm.addEventListener("submit", submitVoucherForm);
		console.log('凭证生成表单事件已绑定');
	} else {
		console.error('未找到凭证生成表单');
	}

	// 绑定摘要翻译表单
	const translateForm = document.getElementById("translate-form");
	if (translateForm) {
		translateForm.addEventListener("submit", submitTranslateForm);
		console.log('摘要翻译表单事件已绑定');
	} else {
		console.error('未找到摘要翻译表单');
	}

	console.log('应用初始化完成');
});
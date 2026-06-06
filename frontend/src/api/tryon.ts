/**
 * AI 试穿 API 封装
 */
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface TryOnResponse {
  task_id: string;
  status: string;
  result_image: string | null;
  message: string | null;
}

export interface ImageUploadResponse {
  filename: string;
  url: string;
  width: number;
  height: number;
  size: number;
}

/**
 * 上传图片
 */
export async function uploadImage(file: File): Promise<ImageUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/images/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "上传失败");
  }

  return res.json();
}

/**
 * 执行虚拟试穿（两步异步模式）
 * 1. 提交任务 → 获取 task_id
 * 2. 轮询状态 → 获取结果
 */
export async function runTryOn(
  clothingImage: string,
  modelImage: string,
  category: string = "upper_body",
  onProgress?: (msg: string) => void
): Promise<TryOnResponse> {
  // Step 1: 提交任务
  const res = await fetch(`${API_BASE}/api/tryon/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      clothing_image: clothingImage,
      model_image: modelImage,
      category,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "试穿请求失败");
  }

  const data: TryOnResponse = await res.json();

  // 如果已直接返回结果（mock 模式），无需轮询
  if (data.status === "completed" || data.status === "failed") {
    return data;
  }

  // Step 2: 轮询状态（DashScope 异步模式）
  const taskId = data.task_id;
  onProgress?.("AI 处理中...");

  for (let i = 0; i < 40; i++) {
    await sleep(3000); // 每 3 秒轮询一次

    const pollRes = await fetch(`${API_BASE}/api/tryon/status/${taskId}`);
    if (!pollRes.ok) continue;

    const pollData: TryOnResponse = await pollRes.json();

    if (pollData.status === "completed") {
      return pollData;
    }
    if (pollData.status === "failed") {
      throw new Error(pollData.message || "处理失败");
    }

    // 更新进度
    const msg = pollData.message || "";
    onProgress?.(msg);
  }

  throw new Error("处理超时，请重试");
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 获取结果图片完整 URL
 */
export function getImageUrl(path: string): string {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

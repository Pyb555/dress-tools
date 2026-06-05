/**
 * AI 试穿 API 封装
 * 生产环境通过 VITE_API_URL 环境变量配置后端地址
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
 * 执行虚拟试穿
 */
export async function runTryOn(
  clothingImage: string,
  modelImage: string,
  category: string = "upper_body"
): Promise<TryOnResponse> {
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

  return res.json();
}

/**
 * 获取结果图片完整 URL
 */
export function getImageUrl(path: string): string {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

import { useState } from "react";
import ImageUploader from "../components/ImageUploader";
import TryOnResult from "../components/TryOnResult";
import { uploadImage, runTryOn, getImageUrl } from "../api/tryon";

type TryOnStatus = "idle" | "loading" | "completed" | "failed";

const CATEGORIES = [
  { value: "upper_body", label: "上衣" },
  { value: "lower_body", label: "下装" },
  { value: "dresses", label: "连衣裙" },
];

/**
 * 主页：完整的 AI 试穿流程
 */
export default function HomePage() {
  // 衣服
  const [clothingFile, setClothingFile] = useState<File | null>(null);
  const [clothingPreview, setClothingPreview] = useState<string | null>(null);
  // 模特
  const [modelFile, setModelFile] = useState<File | null>(null);
  const [modelPreview, setModelPreview] = useState<string | null>(null);
  // 类别
  const [category, setCategory] = useState("upper_body");
  // 结果
  const [status, setStatus] = useState<TryOnStatus>("idle");
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleClothingChange = (file: File) => {
    setClothingFile(file);
    setClothingPreview(URL.createObjectURL(file));
    setStatus("idle");
  };

  const handleModelChange = (file: File) => {
    setModelFile(file);
    setModelPreview(URL.createObjectURL(file));
    setStatus("idle");
  };

  const handleTryOn = async () => {
    if (!clothingFile || !modelFile) {
      alert("请先上传衣服和模特图片");
      return;
    }

    setStatus("loading");
    setMessage(null);

    try {
      // Step 1: 上传两张图片
      const clothingRes = await uploadImage(clothingFile);
      const modelRes = await uploadImage(modelFile);

      // Step 2: 执行试穿
      const result = await runTryOn(clothingRes.filename, modelRes.filename, category);

      if (result.status === "completed" && result.result_image) {
        setResultUrl(getImageUrl(`/results/${result.result_image}`));
        setStatus("completed");
      } else {
        setStatus("failed");
        setMessage(result.message || "未知错误");
      }
    } catch (err) {
      setStatus("failed");
      setMessage(err instanceof Error ? err.message : "请求失败");
    }
  };

  return (
    <div className="home-page">
      <header className="app-header">
        <h1>👗 AI 虚拟试穿</h1>
        <p className="subtitle">上传衣服照片，看看穿在身上的效果</p>
      </header>

      <main className="app-main">
        {/* 上传区域 */}
        <section className="upload-section">
          <ImageUploader
            label="📦 上传衣服图片"
            imageUrl={clothingPreview}
            onImageChange={handleClothingChange}
            placeholder="拖拽或点击上传衣服照片"
          />

          <div className="category-selector">
            <label>衣服类型：</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <ImageUploader
            label="🧑 上传模特图片"
            imageUrl={modelPreview}
            onImageChange={handleModelChange}
            placeholder="拖拽或点击上传人物照片"
          />

          <button
            className="tryon-btn"
            onClick={handleTryOn}
            disabled={status === "loading" || !clothingFile || !modelFile}
          >
            {status === "loading" ? "⏳ 处理中..." : "✨ 开始试穿"}
          </button>
        </section>

        {/* 结果区域 */}
        <TryOnResult
          status={status}
          resultUrl={resultUrl}
          clothingUrl={clothingPreview}
          modelUrl={modelPreview}
          message={message}
        />
      </main>
    </div>
  );
}

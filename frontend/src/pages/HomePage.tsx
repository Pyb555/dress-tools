import { useState, useEffect } from "react";
import ImageUploader from "../components/ImageUploader";
import TryOnResult from "../components/TryOnResult";
import HistoryPanel from "../components/HistoryPanel";
import { uploadImage, runTryOn, getImageUrl } from "../api/tryon";

type TryOnStatus = "idle" | "loading" | "completed" | "failed";

interface HistoryItem {
  id: string;
  date: string;
  clothing_image: string;
  model_image: string;
  result_image: string;
  category: string;
  status: string;
}

const CATEGORIES = [
  { value: "upper_body", label: "上衣" },
  { value: "lower_body", label: "下装" },
  { value: "dresses", label: "连衣裙" },
];

/**
 * 生成简单的预设模特 SVG（Data URI）
 */
function getPresetModel(index: number): string {
  const colors = ["#f5c6cb", "#c3e6cb", "#bee5eb", "#ffeaa7", "#d4c5e2"];
  const skinTones = ["#fdd9b5", "#e8b88a", "#c68e60", "#f0c8a0"];
  const hairColors = ["#2c1810", "#4a3728", "#1a1a2e", "#8b4513", "#3c1414"];
  const c = colors[index % colors.length];
  const s = skinTones[index % skinTones.length];
  const h = hairColors[index % hairColors.length];

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 400" width="200" height="400">
    <rect width="200" height="400" fill="#f0f0f0"/>
    <!-- 头发 -->
    <ellipse cx="100" cy="48" rx="32" ry="34" fill="${h}"/>
    <!-- 脸 -->
    <ellipse cx="100" cy="58" rx="24" ry="28" fill="${s}"/>
    <!-- 脖子 -->
    <rect x="92" y="82" width="16" height="18" fill="${s}" rx="4"/>
    <!-- 身体/衣服 -->
    <rect x="55" y="96" width="90" height="140" fill="${c}" rx="12"/>
    <!-- 肩膀弧线 -->
    <ellipse cx="100" cy="98" rx="55" ry="18" fill="${c}"/>
    <!-- 左臂 -->
    <rect x="30" y="100" width="28" height="100" fill="${c}" rx="10"/>
    <!-- 右臂 -->
    <rect x="142" y="100" width="28" height="100" fill="${c}" rx="10"/>
    <!-- 裤子/下身 -->
    <rect x="60" y="230" width="35" height="130" fill="#3a3a5c" rx="6"/>
    <rect x="105" y="230" width="35" height="130" fill="#3a3a5c" rx="6"/>
  </svg>`;
  return "data:image/svg+xml," + encodeURIComponent(svg);
}

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
  // 预设模特
  const [presetIndex, setPresetIndex] = useState(0);
  const [usePreset, setUsePreset] = useState(false);
  // 类别
  const [category, setCategory] = useState("upper_body");
  // 结果
  const [status, setStatus] = useState<TryOnStatus>("idle");
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  // 历史刷新信号
  const [historyRefresh, setHistoryRefresh] = useState(0);

  const handleClothingChange = (file: File) => {
    setClothingFile(file);
    setClothingPreview(URL.createObjectURL(file));
    setStatus("idle");
  };

  const handleModelChange = (file: File) => {
    setModelFile(file);
    setModelPreview(URL.createObjectURL(file));
    setStatus("idle");
    setUsePreset(false);
  };

  // 切换预设模特
  const handlePresetChange = (idx: number) => {
    setPresetIndex(idx);
    const dataUri = getPresetModel(idx);
    setModelPreview(dataUri);
    setUsePreset(true);
    setStatus("idle");

    // 将 data URI 转为 File 对象
    fetch(dataUri)
      .then((res) => res.blob())
      .then((blob) => {
        setModelFile(new File([blob], `preset_model_${idx + 1}.png`, { type: "image/png" }));
      });
  };

  // 从历史记录加载
  const handleHistorySelect = (item: HistoryItem) => {
    setClothingPreview(getImageUrl(`/uploads/${item.clothing_image}`));
    setModelPreview(getImageUrl(`/uploads/${item.model_image}`));
    setResultUrl(getImageUrl(`/results/${item.result_image}`));
    setStatus("completed");
    setTaskId(item.id);
  };

  const handleTryOn = async () => {
    if (!clothingFile || !modelFile) {
      alert("请先上传衣服和模特图片");
      return;
    }

    setStatus("loading");
    setMessage(null);

    try {
      const clothingRes = await uploadImage(clothingFile);
      const modelRes = await uploadImage(modelFile);
      const result = await runTryOn(clothingRes.filename, modelRes.filename, category);

      if (result.status === "completed" && result.result_image) {
        setResultUrl(getImageUrl(`/results/${result.result_image}`));
        setTaskId(result.task_id);
        setStatus("completed");
        setHistoryRefresh((n) => n + 1);
      } else {
        setStatus("failed");
        setMessage(result.message || "未知错误");
      }
    } catch (err) {
      setStatus("failed");
      setMessage(err instanceof Error ? err.message : "请求失败");
    }
  };

  // 初始化预设模特
  useEffect(() => {
    if (!modelPreview && !usePreset) {
      handlePresetChange(0);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="home-page">
      <header className="app-header">
        <h1>👗 AI 虚拟试穿</h1>
        <p className="subtitle">上传衣服照片，看看穿在身上的效果</p>
      </header>

      <main className="app-main">
        {/* 上传区域 */}
        <section className="upload-section">
          <div className="upload-column">
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
          </div>

          <div className="upload-column">
            <ImageUploader
              label="🧑 上传模特图片"
              imageUrl={modelPreview}
              onImageChange={handleModelChange}
              placeholder="拖拽或点击上传人物照片"
            />
            <div className="preset-models">
              <span className="preset-label">
                快速体验{usePreset ? " ✅" : ""}：
              </span>
              <div className="preset-list">
                {[0, 1, 2, 3, 4].map((idx) => (
                  <div
                    key={idx}
                    className={`preset-item ${presetIndex === idx && usePreset ? "active" : ""}`}
                    onClick={() => handlePresetChange(idx)}
                  >
                    <img src={getPresetModel(idx)} alt={`模特 ${idx + 1}`} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <button
          className="tryon-btn"
          onClick={handleTryOn}
          disabled={status === "loading" || !clothingFile || !modelFile}
        >
          {status === "loading" ? "⏳ AI 试穿中..." : "✨ 开始试穿"}
        </button>

        {/* 结果区域 */}
        <TryOnResult
          status={status}
          resultUrl={resultUrl}
          clothingUrl={clothingPreview}
          modelUrl={modelPreview}
          message={message}
        />

        {/* 如果成功，显示下载按钮 */}
        {status === "completed" && resultUrl && (
          <div className="result-actions">
            <a
              href={resultUrl}
              download={`tryon_${taskId}.png`}
              className="download-btn"
            >
              💾 下载结果
            </a>
            <button
              className="retry-btn"
              onClick={() => {
                setStatus("idle");
                setResultUrl(null);
              }}
            >
              🔄 再试一次
            </button>
          </div>
        )}

        {/* 历史记录 */}
        <HistoryPanel
          refreshTrigger={historyRefresh}
          onSelect={handleHistorySelect}
        />
      </main>

      <footer className="app-footer">
        <p>
          AI 虚拟试穿 · Powered by{" "}
          <a href="https://github.com/Pyb555/dress-tools" target="_blank" rel="noopener">
            Dress Tools
          </a>
        </p>
      </footer>
    </div>
  );
}

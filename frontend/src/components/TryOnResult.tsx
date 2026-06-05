interface Props {
  status: "idle" | "loading" | "completed" | "failed";
  resultUrl: string | null;
  clothingUrl: string | null;
  modelUrl: string | null;
  message: string | null;
}

/**
 * 试穿结果展示：原图对比 + 生成结果
 */
export default function TryOnResult({ status, resultUrl, clothingUrl, modelUrl, message }: Props) {
  if (status === "idle") {
    return (
      <div className="result-section result-idle">
        <div className="result-placeholder">
          <span className="result-icon">👗</span>
          <p>上传衣服和模特图片，然后点击"开始试穿"</p>
        </div>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div className="result-section result-loading">
        <div className="loading-spinner" />
        <p>AI 正在生成试穿效果...</p>
        <p className="loading-hint">这可能需要几秒钟，请耐心等待</p>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="result-section result-failed">
        <span className="result-icon">❌</span>
        <p>试穿失败</p>
        {message && <p className="error-message">{message}</p>}
      </div>
    );
  }

  return (
    <div className="result-section result-completed">
      <h3>试穿效果</h3>
      <div className="result-comparison">
        {clothingUrl && (
          <div className="comparison-item">
            <p className="comparison-label">衣服</p>
            <img src={clothingUrl} alt="衣服" />
          </div>
        )}
        {modelUrl && (
          <div className="comparison-item">
            <p className="comparison-label">模特</p>
            <img src={modelUrl} alt="模特" />
          </div>
        )}
        {resultUrl && (
          <div className="comparison-item result-highlight">
            <p className="comparison-label">✨ 试穿效果</p>
            <img src={resultUrl} alt="试穿效果" />
          </div>
        )}
      </div>
    </div>
  );
}

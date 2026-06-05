import { useState, useEffect } from "react";
import { getImageUrl } from "../api/tryon";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface HistoryItem {
  id: string;
  date: string;
  clothing_image: string;
  model_image: string;
  result_image: string;
  category: string;
  status: string;
}

interface Props {
  refreshTrigger: number;  // 外部刷新信号
  onSelect: (item: HistoryItem) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  upper_body: "上衣",
  lower_body: "下装",
  dresses: "连衣裙",
};

const STORAGE_KEY = "dress-tools-history";

/**
 * 历史记录面板 - 从 localStorage 读取本地记录 + 服务端同步
 */
export default function HistoryPanel({ refreshTrigger, onSelect }: Props) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    loadHistory();
  }, [refreshTrigger]);

  const loadHistory = async () => {
    // 先从本地读取
    const local = loadLocalHistory();
    setItems(local);

    // 尝试从服务端同步（静默失败）
    try {
      const res = await fetch(`${API_BASE}/api/history/list?limit=20`);
      if (res.ok) {
        const data = await res.json();
        if (data.items?.length > 0) {
          setItems(data.items);
          // 同步到本地
          saveLocalHistory(data.items);
        }
      }
    } catch {
      // 服务端不可用时使用本地数据
    }
  };

  const clearHistory = async () => {
    if (!confirm("确定清空所有历史记录？")) return;
    setItems([]);
    clearLocalHistory();
    try {
      await fetch(`${API_BASE}/api/history/clear`, { method: "DELETE" });
    } catch { /* ignore */ }
  };

  const deleteItem = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const updated = items.filter((item) => item.id !== id);
    setItems(updated);
    saveLocalHistory(updated);
    try {
      await fetch(`${API_BASE}/api/history/${id}`, { method: "DELETE" });
    } catch { /* ignore */ }
  };

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      const now = new Date();
      const diff = now.getTime() - d.getTime();
      if (diff < 60000) return "刚刚";
      if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
      if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
      return d.toLocaleDateString("zh-CN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className={`history-panel ${expanded ? "expanded" : ""}`}>
      <div className="history-header" onClick={() => setExpanded(!expanded)}>
        <h3>📜 历史记录 ({items.length})</h3>
        <span className="history-toggle">{expanded ? "收起 ▲" : "展开 ▼"}</span>
      </div>

      {expanded && (
        <div className="history-body">
          {items.length === 0 ? (
            <p className="history-empty">暂无试穿记录</p>
          ) : (
            <>
              <div className="history-list">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="history-item"
                    onClick={() => onSelect(item)}
                  >
                    <img
                      src={getImageUrl(`/results/${item.result_image}`)}
                      alt={`试穿结果 ${item.id}`}
                      className="history-thumb"
                      loading="lazy"
                    />
                    <div className="history-info">
                      <span className="history-category">
                        {CATEGORY_LABELS[item.category] || item.category}
                      </span>
                      <span className="history-date">{formatDate(item.date)}</span>
                    </div>
                    <button
                      className="history-delete"
                      onClick={(e) => deleteItem(e, item.id)}
                      title="删除"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
              <button className="history-clear-btn" onClick={clearHistory}>
                清空全部记录
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ========== localStorage helpers ==========

function loadLocalHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveLocalHistory(items: HistoryItem[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 50)));
  } catch { /* storage full */ }
}

function clearLocalHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch { /* ignore */ }
}

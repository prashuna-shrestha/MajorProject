"use client";

import { useTheme } from "@mui/material";

//====================
// 1. Type Definitions
//====================
type NewsItem = {
  title: string;
  summary: string;
  source: string;
  url: string;
  image?: string;
  publishedAt?: string;
};

//====================
// 2. Helper Functions
//====================

// Convert ISO date to relative "time ago" string
function timeAgo(date: string) {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);

  const intervals = [
    { label: "year", seconds: 31536000 },
    { label: "month", seconds: 2592000 },
    { label: "day", seconds: 86400 },
    { label: "hour", seconds: 3600 },
    { label: "minute", seconds: 60 },
  ];

  for (const i of intervals) {
    const count = Math.floor(seconds / i.seconds);
    if (count >= 1)
      return `${count} ${i.label}${count > 1 ? "s" : ""} ago`;
  }

  return "Just now";
}

//====================
// 3. Main Component
//====================
export default function NewsGrid({ news }: { news: NewsItem[] }) {

  // ✅ Get theme from MUI (Redux controlled)
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";

  // Theme-aware colors (now based on MUI theme)
  const colors = {
    cardBg: theme.palette.background.paper,
    border: theme.palette.divider,
    textPrimary: theme.palette.text.primary,
    textSecondary: theme.palette.text.secondary,
    badgeBg: isDark ? "#1f2937" : "#f1f5f9",
    badgeText: theme.palette.text.primary,
    timeText: theme.palette.text.secondary,
    link: theme.palette.primary.main,
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
        gap: "20px",
      }}
    >
      {news.map((item, idx) => (
        <div
          key={idx}
          style={{
            background: colors.cardBg,
            borderRadius: "14px",
            overflow: "hidden",
            border: `1px solid ${colors.border}`,
            transition: "all 0.25s ease",
          }}
        >
          {/* IMAGE */}
          <div style={{ height: "180px", overflow: "hidden" }}>
            <img
              src={item.image || "/placeholder.jpg"}
              alt={item.title}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
          </div>

          {/* CONTENT */}
          <div
            style={{
              padding: "24px",
              background: theme.palette.background.default,
            }}
          >
            {/* Source & Time */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "12px",
                marginBottom: "6px",
              }}
            >
              <span
                style={{
                  background: colors.badgeBg,
                  color: colors.badgeText,
                  padding: "3px 8px",
                  borderRadius: "6px",
                  fontWeight: 600,
                }}
              >
                {item.source}
              </span>

              {item.publishedAt && (
                <span style={{ color: colors.timeText }}>
                  {timeAgo(item.publishedAt)}
                </span>
              )}
            </div>

            {/* Title */}
            <h3
              style={{
                fontSize: "17px",
                fontWeight: 600,
                color: colors.textPrimary,
              }}
            >
              {item.title}
            </h3>

            {/* Summary */}
            <p
              style={{
                fontSize: "14px",
                color: colors.textSecondary,
              }}
            >
              {item.summary}
            </p>

            {/* Link */}
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: colors.link }}
            >
              Read more →
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
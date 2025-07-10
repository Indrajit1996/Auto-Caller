import React, { useState } from "react";

function toUTCISOString(localDateString) {
  if (!localDateString) return "";
  const localDate = new Date(localDateString);
  return localDate.toISOString().slice(0, 19) + "Z";
}

export default function ScheduleCallForm() {
  const [to, setTo] = useState("");
  const [message, setMessage] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [utcInput, setUtcInput] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Scheduling...");
    // Use UTC input if provided, otherwise convert local time
    const utcISOString = utcInput.trim() ? utcInput.trim() : toUTCISOString(scheduledTime);
    try {
      const res = await fetch("/api/schedule-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to,
          message,
          scheduled_time: utcISOString
        }),
      });
      const data = await res.json();
      if (data.status === "scheduled") {
        setStatus("Call scheduled successfully!");
      } else {
        setStatus("Failed to schedule call.");
      }
    } catch (err) {
      setStatus("Error: " + err.message);
    }
  };

  const utcTime = toUTCISOString(scheduledTime);

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 400, margin: "2rem auto", padding: 20, border: "1px solid #ccc", borderRadius: 8 }}>
      <h2>Schedule a Call</h2>
      <label style={{ display: "block", marginBottom: 8 }}>
        Phone Number:
        <input value={to} onChange={e => setTo(e.target.value)} required style={{ width: "100%", marginTop: 4 }} />
      </label>
      <label style={{ display: "block", marginBottom: 8 }}>
        Message:
        <input value={message} onChange={e => setMessage(e.target.value)} required style={{ width: "100%", marginTop: 4 }} />
      </label>
      <label style={{ display: "block", marginBottom: 8 }}>
        Schedule Time (your local time):
        <input
          type="datetime-local"
          value={scheduledTime}
          onChange={e => setScheduledTime(e.target.value)}
          style={{ width: "100%", marginTop: 4 }}
        />
      </label>
      {scheduledTime && (
        <div style={{ marginBottom: 8, fontSize: 13, color: '#555' }}>
          <strong>UTC Time to be scheduled:</strong> {utcTime}
        </div>
      )}
      <label style={{ display: "block", marginBottom: 8 }}>
        Or enter UTC time directly (format: YYYY-MM-DDTHH:MM:SSZ):
        <input
          type="text"
          placeholder="2025-07-10T14:51:00Z"
          value={utcInput}
          onChange={e => setUtcInput(e.target.value)}
          style={{ width: "100%", marginTop: 4 }}
        />
      </label>
      <button type="submit" style={{ width: "100%", padding: 10, background: "#1976d2", color: "white", border: "none", borderRadius: 4 }}>Schedule Call</button>
      <div style={{ marginTop: 12, color: status.includes("success") ? "green" : "red" }}>{status}</div>
    </form>
  );
} 
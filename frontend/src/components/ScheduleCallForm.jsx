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
  const [callType, setCallType] = useState("one-time");
  const [recurringTime, setRecurringTime] = useState("");
  const [recurringDays, setRecurringDays] = useState([]);
  const [recurringDate, setRecurringDate] = useState("");
  const [useUtcInput, setUseUtcInput] = useState(false);
  const [utcRecurringTime, setUtcRecurringTime] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Scheduling...");
    
    let payload = {
      to,
      message,
      call_type: callType
    };

    if (callType === "one-time") {
      // Use UTC input if provided, otherwise convert local time
      const utcISOString = utcInput.trim() ? utcInput.trim() : toUTCISOString(scheduledTime);
      payload.scheduled_time = utcISOString;
    } else {
      // Recurring call
      if (recurringDays.length === 0) {
        setStatus("Please select at least one day of the week.");
        return;
      }
      
      if (useUtcInput) {
        // Use direct UTC input
        if (!utcRecurringTime) {
          setStatus("Please enter UTC time for recurring calls.");
          return;
        }
        payload.recurrence_time = utcRecurringTime;
      } else {
        // Convert San Diego time to UTC
        if (!recurringTime) {
          setStatus("Please select a time for recurring calls.");
          return;
        }
        
        if (!recurringDate) {
          setStatus("Please select a start date for recurring calls.");
          return;
        }
        
        // Create a proper date string with the selected date and time
        const [hours, minutes] = recurringTime.split(':');
        const selectedDate = new Date(recurringDate);
        const sanDiegoTime = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate(), parseInt(hours), parseInt(minutes));
        
        // Convert to UTC (San Diego is UTC-7 for PDT, UTC-8 for PST)
        const utcTime = new Date(sanDiegoTime.getTime() + (7 * 60 * 60 * 1000)); // Add 7 hours to convert to UTC
        const utcISOString = utcTime.toISOString().slice(0, 19) + "Z";
        payload.recurrence_time = utcISOString;
      }
      
      payload.recurrence_day = recurringDays;
      payload.recurrence_pattern = "weekly";
    }

    try {
      console.log("Sending payload:", payload);
      const res = await fetch("/api/schedule-call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      console.log("Response status:", res.status);
      const data = await res.json();
      console.log("Response data:", data);
      
      if (res.ok && data.status === "scheduled") {
        setStatus("Call scheduled successfully!");
      } else {
        setStatus("Failed to schedule call: " + (data.detail || data.message || "Unknown error"));
      }
    } catch (err) {
      console.error("Error:", err);
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
        Call Type:
        <select value={callType} onChange={e => setCallType(e.target.value)} style={{ width: "100%", marginTop: 4 }}>
          <option value="one-time">One-time Call</option>
          <option value="recurring">Recurring Call</option>
        </select>
      </label>
      {callType === "one-time" ? (
        <>
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
        </>
              ) : (
          <>
            <label style={{ display: "block", marginBottom: 8 }}>
              Time Input Method:
              <select value={useUtcInput ? "utc" : "local"} onChange={e => setUseUtcInput(e.target.value === "utc")} style={{ width: "100%", marginTop: 4 }}>
                <option value="local">San Diego Time (Auto-convert to UTC)</option>
                <option value="utc">Direct UTC Time Input</option>
              </select>
            </label>
            
            {useUtcInput ? (
              <label style={{ display: "block", marginBottom: 8 }}>
                UTC Time (format: YYYY-MM-DDTHH:MM:SSZ):
                <input
                  type="text"
                  placeholder="2025-07-11T14:37:00Z"
                  value={utcRecurringTime}
                  onChange={e => setUtcRecurringTime(e.target.value)}
                  style={{ width: "100%", marginTop: 4 }}
                />
              </label>
            ) : (
              <>
                <label style={{ display: "block", marginBottom: 8 }}>
                  Start Date:
                  <input
                    type="date"
                    value={recurringDate}
                    onChange={e => setRecurringDate(e.target.value)}
                    style={{ width: "100%", marginTop: 4 }}
                  />
                </label>
                <label style={{ display: "block", marginBottom: 8 }}>
                  Time (San Diego time):
                  <input
                    type="time"
                    value={recurringTime}
                    onChange={e => setRecurringTime(e.target.value)}
                    style={{ width: "100%", marginTop: 4 }}
                  />
                </label>
              </>
            )}
            <label style={{ display: "block", marginBottom: 8 }}>
              Days of the week:
              <div style={{ marginTop: 4 }}>
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, index) => (
                  <label key={day} style={{ display: 'inline-block', marginRight: 10 }}>
                    <input
                      type="checkbox"
                      checked={recurringDays.includes(index)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setRecurringDays([...recurringDays, index]);
                        } else {
                          setRecurringDays(recurringDays.filter(d => d !== index));
                        }
                      }}
                    />
                    {day}
                  </label>
                ))}
              </div>
            </label>
          </>
        )}
      <button type="submit" style={{ width: "100%", padding: 10, background: "#1976d2", color: "white", border: "none", borderRadius: 4 }}>Schedule Call</button>
      <div style={{ marginTop: 12, color: status.includes("success") ? "green" : "red" }}>{status}</div>
    </form>
  );
} 
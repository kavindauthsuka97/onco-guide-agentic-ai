import { useEffect, useState } from "react";

import {
  getPendingReviews,
  approveReview,
  rejectReview,
  editApproveReview,
} from "../services/api";

export default function ReviewDashboard() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [editingReviewId, setEditingReviewId] = useState(null);
  const [editedAnswer, setEditedAnswer] = useState("");

  async function loadReviews() {
    setLoading(true);
    setStatusMessage("");

    try {
      const data = await getPendingReviews();
      setReviews(data.items || []);
    } catch (error) {
      setStatusMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(reviewId) {
    try {
      await approveReview(reviewId, "Approved from React dashboard.");
      setStatusMessage("Review approved.");
      await loadReviews();
    } catch (error) {
      setStatusMessage(`Error: ${error.message}`);
    }
  }

  async function handleReject(reviewId) {
    try {
      await rejectReview(reviewId, "Rejected from React dashboard.");
      setStatusMessage("Review rejected.");
      await loadReviews();
    } catch (error) {
      setStatusMessage(`Error: ${error.message}`);
    }
  }

  function startEditing(review) {
    setEditingReviewId(review.review_id);
    setEditedAnswer(review.draft_answer || "");
  }

  async function handleEditApprove(reviewId) {
    if (!editedAnswer.trim()) {
      setStatusMessage("Edited answer cannot be empty.");
      return;
    }

    try {
      await editApproveReview(
        reviewId,
        editedAnswer,
        "Edited and approved from React dashboard."
      );

      setStatusMessage("Review edited and approved.");
      setEditingReviewId(null);
      setEditedAnswer("");
      await loadReviews();
    } catch (error) {
      setStatusMessage(`Error: ${error.message}`);
    }
  }

  useEffect(() => {
    loadReviews();
  }, []);

  return (
    <div className="review-page">
      <div className="review-header">
        <div>
          <h2>Human Review Dashboard</h2>
          <p>Review high-risk or low-confidence medical AI responses before final release.</p>
        </div>

        <button className="secondary-button" onClick={loadReviews} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {statusMessage && <div className="status-box">{statusMessage}</div>}

      {reviews.length === 0 ? (
        <div className="empty-review">
          No pending human review cases.
        </div>
      ) : (
        <div className="review-list">
          {reviews.map((review) => (
            <div className="review-card" key={review.review_id}>
              <div className="review-meta">
                <span>Review ID: {review.review_id}</span>
                <span>Status: {review.status}</span>
                <span>Agent: {review.selected_agent}</span>
                <span>Risk: {review.input_risk_level}</span>
              </div>

              <div className="review-section">
                <h3>User message</h3>
                <p>{review.user_message}</p>
              </div>

              <div className="review-section">
                <h3>Draft answer</h3>
                <p>{review.draft_answer}</p>
              </div>

              <div className="review-section">
                <h3>Review reason</h3>
                <p>{review.human_review_reason}</p>
              </div>

              {editingReviewId === review.review_id ? (
                <div className="review-section">
                  <h3>Edit final answer</h3>

                  <textarea
                    className="edit-textarea"
                    value={editedAnswer}
                    onChange={(event) => setEditedAnswer(event.target.value)}
                  />

                  <div className="review-actions">
                    <button
                      className="approve-button"
                      onClick={() => handleEditApprove(review.review_id)}
                    >
                      Save & Approve
                    </button>

                    <button
                      className="secondary-button"
                      onClick={() => {
                        setEditingReviewId(null);
                        setEditedAnswer("");
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="review-actions">
                  <button
                    className="approve-button"
                    onClick={() => handleApprove(review.review_id)}
                  >
                    Approve
                  </button>

                  <button
                    className="edit-button"
                    onClick={() => startEditing(review)}
                  >
                    Edit & Approve
                  </button>

                  <button
                    className="reject-button"
                    onClick={() => handleReject(review.review_id)}
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
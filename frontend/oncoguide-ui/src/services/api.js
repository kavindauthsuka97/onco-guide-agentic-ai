import { fetchEventSource } from "@microsoft/fetch-event-source";

const API_BASE_URL = "http://127.0.0.1:8000";

class StopStreamError extends Error {}

export async function sendMessage(message, conversationId = null) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: message,
      conversation_id: conversationId,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    const errorMessage =
      data?.detail?.error ||
      data?.detail ||
      data?.error ||
      "API request failed";

    throw new Error(
      typeof errorMessage === "string"
        ? errorMessage
        : JSON.stringify(errorMessage)
    );
  }

  return data;
}

export async function streamMessage({
  message,
  conversationId = null,
  onStart,
  onProgress,
  onFinal,
  onError,
}) {
  const controller = new AbortController();

  try {
    await fetchEventSource(`${API_BASE_URL}/chat/stream`, {
      method: "POST",
      signal: controller.signal,
      openWhenHidden: true,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        conversation_id: conversationId,
      }),

      async onopen(response) {
        if (!response.ok) {
          throw new Error(`Stream failed with status ${response.status}`);
        }
      },

      onmessage(event) {
        const data = JSON.parse(event.data);

        if (event.event === "start") {
          onStart?.(data);
        }

        if (event.event === "progress") {
          onProgress?.(data);
        }

        if (event.event === "final") {
          onFinal?.(data);
          controller.abort();
          throw new StopStreamError("Stream completed.");
        }

        if (event.event === "error") {
          onError?.(data);
          controller.abort();
          throw new StopStreamError("Stream ended with error.");
        }
      },

      onerror(error) {
        if (error instanceof StopStreamError) {
          throw error;
        }

        onError?.({
          message: error.message || "Streaming failed",
        });

        throw error;
      },
    });
  } catch (error) {
    if (error instanceof StopStreamError) {
      return;
    }

    throw error;
  }
}

export async function getPendingReviews() {
  const response = await fetch(`${API_BASE_URL}/review/pending`);

  if (!response.ok) {
    throw new Error("Failed to load pending reviews");
  }

  return await response.json();
}

export async function approveReview(reviewId, comment = "") {
  const response = await fetch(`${API_BASE_URL}/review/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      review_id: reviewId,
      comment: comment,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to approve review");
  }

  return await response.json();
}

export async function rejectReview(reviewId, comment = "") {
  const response = await fetch(`${API_BASE_URL}/review/reject`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      review_id: reviewId,
      comment: comment,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to reject review");
  }

  return await response.json();
}

export async function editApproveReview(reviewId, finalAnswer, comment = "") {
  const response = await fetch(`${API_BASE_URL}/review/edit-approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      review_id: reviewId,
      final_answer: finalAnswer,
      comment: comment,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to edit and approve review");
  }

  return await response.json();
}
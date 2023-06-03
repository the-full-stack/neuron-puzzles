let puzzles;

async function makeRequest(path, method = "GET") {
  const response = await fetch(path, {
    method,
    mode: "cors",
    headers: { "Content-Type": "application/json" },
  });
  return response.json();
}

async function getPuzzle() {
  puzzles = await makeRequest("/puzzles");
  const { _id: puzzleId } = puzzles[0];
  return makeRequest(`/puzzles/${puzzleId}`);
}

function createAnnotatedSpan(content) {
  const span = document.createElement("span");
  span.classList.add("tokens");
  if (Array.isArray(content)) {
    const [text, number] = content;
    span.innerText = text;
    span.classList.add(`tokens-${number}`);
  } else {
    span.innerText = content;
  }
  return span;
}

function createPuzzleFrom(activationRecord) {
  const p = document.createElement("p");
  activationRecord.forEach((record) =>
    p.appendChild(createAnnotatedSpan(record))
  );
  return p;
}

document.addEventListener("DOMContentLoaded", () => {
  const puzzleTexts = document.getElementById("puzzle-texts");
  getPuzzle().then(({ activationRecords }) => {
    activationRecords.forEach((record) =>
      puzzleTexts.appendChild(createPuzzleFrom(record))
    );
  });
});

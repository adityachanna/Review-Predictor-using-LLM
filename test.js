import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

async function run() {
    const response = await ai.models.generateContent({
        model: "gemini-3-pro-preview",
        contents: "Find the race condition in this multi-threaded C++ snippet: [code here]",
    });

    console.log(response.text);
}

run();

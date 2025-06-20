import fs from "fs";
import path from "path";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).end();

  const { phone, lang, source, timestamp } = req.body;

  const newEntry = {
    phone,
    lang,
    source: source || "unknown",
    timestamp: timestamp || new Date().toISOString(),
  };

  const filePath = path.resolve("data.json");

  let existing = [];
  try {
    if (fs.existsSync(filePath)) {
      const fileContent = fs.readFileSync(filePath, "utf-8");
      existing = JSON.parse(fileContent);
    }
  } catch (e) {
    console.error("Dosya okuma hatası", e);
  }

  existing.push(newEntry);

  try {
    fs.writeFileSync(filePath, JSON.stringify(existing, null, 2));
    return res.status(200).json({ success: true });
  } catch (e) {
    console.error("Yazma hatası", e);
    return res.status(500).json({ error: "Yazma hatası" });
  }
}

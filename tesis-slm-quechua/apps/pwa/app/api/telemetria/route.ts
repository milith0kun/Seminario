import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { id_interaccion, pregunta, respuesta, modo, valoracion, correccion_usuario } = body;

    const record = {
      timestamp: new Date().toISOString(),
      id_interaccion: id_interaccion || `loc-${Date.now()}`,
      pregunta,
      respuesta,
      modo: modo || "E4_rag_reglas",
      valoracion: valoracion || "like",
      correccion_usuario: correccion_usuario || null,
    };

    // Intentar escribir en datos/entrenamiento/telemetria_interacciones.jsonl
    try {
      const outDir = path.join(process.cwd(), "..", "..", "datos", "entrenamiento");
      if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
      }
      const outFile = path.join(outDir, "telemetria_interacciones.jsonl");
      fs.appendFileSync(outFile, JSON.stringify(record, null, 0) + "\n", "utf-8");
    } catch (err) {
      console.warn("No se pudo escribir en archivo local, guardado en log:", err);
    }

    return NextResponse.json({ status: "ok", mensaje: "Telemetría registrada exitosamente." });
  } catch (error: any) {
    return NextResponse.json(
      { status: "error", detail: error?.message || "Error registrando telemetría" },
      { status: 400 }
    );
  }
}

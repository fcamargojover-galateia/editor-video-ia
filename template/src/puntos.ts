// Lo genera scripts/seguir.py. Posiciones en % del cuadro; null = no se ve en ese momento.
// Izquierda/derecha son las de la PANTALLA.
export const PASO = 0.1;
export type Punto = [number, number] | null;
export type Gesto = "abierta" | "puno" | "senala" | "pinza" | "pulgar";
export const PUNTOS: Record<string, Punto[]> = {};
export const GESTOS: { t: number; mano: "izq" | "der"; gesto: Gesto }[] = [];

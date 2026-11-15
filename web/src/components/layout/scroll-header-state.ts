export interface HeaderScrollState {
  y: number;
  upwardDistance: number;
  mode: "top" | "hidden" | "floating";
}

export function initialHeaderState(y: number): HeaderScrollState {
  y = Math.max(0, y);
  return { y, upwardDistance: 0, mode: y <= 80 ? "top" : "hidden" };
}

export function nextHeaderState(state: HeaderScrollState, y: number): HeaderScrollState {
  y = Math.max(0, y);
  if (y <= 80) return initialHeaderState(y);
  if (y > state.y) return { y, upwardDistance: 0, mode: "hidden" };
  if (y === state.y) return state;

  const upwardDistance = state.upwardDistance + state.y - y;
  return { y, upwardDistance, mode: upwardDistance >= 8 ? "floating" : state.mode };
}

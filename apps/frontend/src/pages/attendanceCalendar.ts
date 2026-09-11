export function getCalendarCellCount(year: number, month: number) {
  const firstDay = new Date(year, month - 1, 1).getDay();
  const mondayOffset = (firstDay + 6) % 7;
  const daysInMonth = new Date(year, month, 0).getDate();
  return Math.ceil((mondayOffset + daysInMonth) / 7) * 7;
}

export function shiftMonth(year: number, month: number, offset: number) {
  const next = new Date(year, month - 1 + offset, 1);
  return { year: next.getFullYear(), month: next.getMonth() + 1 };
}
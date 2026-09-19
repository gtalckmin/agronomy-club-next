export function normaliseChapterPage(pageParam: string | null): number {
  const page = Number(pageParam);

  return Number.isSafeInteger(page) && page > 0 ? page : 1;
}

export interface Book {
  id: number;
  code: string;
  name: string;
  testament: 'old' | 'new';
  chapterCount: number;
  isAvailable: boolean;
}

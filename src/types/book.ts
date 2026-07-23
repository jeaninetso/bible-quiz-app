export interface Section {
  id: number;
  bookId: number;
  name: string;
  isAvailable: boolean;
}

export interface Book {
  id: number;
  code: string;
  name: string;
  testament: 'old' | 'new';
  chapterCount: number;
  isAvailable: boolean;
  sections: Section[];
}

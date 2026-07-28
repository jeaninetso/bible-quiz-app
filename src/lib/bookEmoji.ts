// Maps each book code (backend/scripts/seed_books.py) to an emoji capturing
// a memorable plot point or image from that book — not generic decoration.
// Falls back to a plain book for any code added without a frontend update,
// so the UI never breaks on an unmapped code.
const BOOK_EMOJI: Record<string, string> = {
  Gen: '🍎', // the forbidden fruit
  Exod: '🌊', // parting of the Red Sea
  Lev: '🐑', // sacrificial system
  Num: '🍇', // the spies' cluster of grapes from Canaan
  Deut: '🏔️', // Moses viewing the promised land from Mount Nebo
  Josh: '🎺', // trumpets at the fall of Jericho
  Judg: '💪', // Samson's strength
  Ruth: '🌾', // gleaning wheat in Boaz's field
  '1Sam': '🪨', // David's sling stone against Goliath
  '2Sam': '🌳', // Absalom caught by his hair in a tree
  '1Kgs': '⚖️', // Solomon's judgment
  '2Kgs': '🔥', // Elijah taken up in a chariot of fire
  '1Chr': '📜', // genealogies
  '2Chr': '🏛️', // Solomon's temple
  Ezra: '🏗️', // rebuilding the temple
  Neh: '🧱', // rebuilding Jerusalem's walls
  Esth: '👑', // Esther becomes queen
  Job: '🌪️', // God answers Job from the whirlwind
  Ps: '🎵', // songs
  Prov: '💡', // wisdom
  Eccl: '💨', // "vanity of vanities" — vapor, fleetingness
  Song: '🌹', // "I am a rose of Sharon"
  Isa: '✨', // "people walking in darkness have seen a great light"
  Jer: '🏺', // the potter and the clay
  Lam: '😢', // weeping over Jerusalem
  Ezek: '🦴', // valley of dry bones
  Dan: '🦁', // the lions' den
  Hos: '💔', // Hosea's unfaithful marriage as a symbol of Israel
  Joel: '🦗', // the locust plague
  Amos: '🌊', // "let justice roll down like waters"
  Obad: '📉', // Edom's pride brought low
  Jonah: '🐳', // swallowed by the great fish
  Mic: '👣', // "walk humbly with your God"
  Nah: '💥', // the fall of Nineveh
  Hab: '🗼', // "I will stand at my watchtower"
  Zeph: '📯', // "a day of trumpet and battle cry"
  Hag: '🏗️', // rebuilding the temple
  Zech: '🕊️', // "not by might nor by power, but by my Spirit"
  Mal: '💰', // "bring the whole tithe"
  Matt: '⭐', // the star of Bethlehem
  Mark: '⚡', // the fast-paced, "immediately" gospel
  Luke: '🐑', // shepherds at the manger
  John: '💧', // water turned to wine, living water
  Acts: '🔥', // tongues of fire at Pentecost
  Rom: '✝️', // justification through the cross
  '1Cor': '❤️', // the love chapter
  '2Cor': '🌵', // Paul's "thorn in the flesh"
  Gal: '🍇', // the fruit of the Spirit
  Eph: '🛡️', // the armor of God
  Phil: '😊', // joy despite imprisonment
  Col: '🌌', // Christ supreme over all creation
  '1Thess': '☁️', // caught up together in the clouds
  '2Thess': '⏳', // waiting for the day of the Lord
  '1Tim': '📋', // instructions for church leadership
  '2Tim': '🏁', // "I have finished the race"
  Titus: '📋', // instructions for church order
  Phlm: '🤝', // Paul's appeal to receive Onesimus as a brother
  Heb: '🏃', // "run with endurance the race set before us"
  Jas: '👅', // taming the tongue
  '1Pet': '🧱', // living stones
  '2Pet': '🌋', // the elements will be destroyed by fire
  '1John': '🕯️', // "God is light"
  '2John': '💌', // a short personal letter
  '3John': '🚪', // hospitality to traveling teachers
  Jude: '⚔️', // "contend for the faith"
  Rev: '👑', // Christ as King of Kings
};

export function bookEmoji(code: string): string {
  return BOOK_EMOJI[code] ?? '📖';
}

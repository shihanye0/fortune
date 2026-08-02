declare module 'lunar-javascript' {
  interface Lunar {
    getMonthInChinese(): string
    getDayInChinese(): string
    getYearInGanZhi(): string
  }

  interface SolarDate {
    getLunar(): Lunar
  }

  export const Solar: {
    fromYmd(year: number, month: number, day: number): SolarDate
  }
}

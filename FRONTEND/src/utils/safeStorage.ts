export function safeGetItem(key: string, fallback: string | null = null): string | null {
  try {
    const item = localStorage.getItem(key);
    return item !== null ? item : fallback;
  } catch (error) {
    console.warn(`Error reading localStorage key "${key}":`, error);
    return fallback;
  }
}

export function safeSetItem(key: string, value: string): boolean {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch (error) {
    console.warn(`Error setting localStorage key "${key}":`, error);
    return false;
  }
}

export function safeRemoveItem(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.warn(`Error removing localStorage key "${key}":`, error);
  }
}

export function safeGetJSON<T>(key: string, fallback: T, validator?: (v: unknown) => boolean): T {
  try {
    const item = localStorage.getItem(key);
    if (item === null) return fallback;
    const parsed = JSON.parse(item);
    if (validator && !validator(parsed)) {
      console.warn(`Validation failed for localStorage key "${key}"`);
      return fallback;
    }
    return parsed as T;
  } catch (error) {
    console.warn(`Error parsing localStorage key "${key}":`, error);
    return fallback;
  }
}

export function safeSetJSON(key: string, value: unknown): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.warn(`Error stringifying localStorage key "${key}":`, error);
    return false;
  }
}

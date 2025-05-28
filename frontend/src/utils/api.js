const MAX_RETRIES = 3;
const INITIAL_DELAY = 1000;

export const retry = async (fn, retries = MAX_RETRIES, delay = INITIAL_DELAY) => {
  try {
    return await fn();
  } catch (error) {
    if (retries === 0) throw error;
    await new Promise((resolve) => setTimeout(resolve, delay));
    return retry(fn, retries - 1, delay * 2);
  }
};

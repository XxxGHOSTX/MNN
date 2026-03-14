// frontend/src/lib/utils.js

/**
 * Utility to join classNames conditionally.
 * @param  {...any} args
 * @returns {string}
 */
export function cn(...args) {
  return args
    .flat(Infinity)
    .filter(Boolean)
    .join(' ');
}

export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Dependabot commit bodies include unwrappable compare-URL lines
    // ("Bumps [x] from a to b." / "- [Commits](https://...)") that
    // routinely exceed the default 100-char limit.
    'body-max-line-length': [0],
  },
};

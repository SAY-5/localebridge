#!/usr/bin/env node
import { Command } from "commander";
import { walk } from "./ast/walker.js";
import { writeJson } from "./output/writer.js";

const program = new Command();
program
  .name("localebridge-extract")
  .description("Extract translatable strings from a React/TypeScript source tree")
  .requiredOption("--src <path>", "source root to walk")
  .requiredOption("--out <path>", "output JSON path")
  .option("--strict", "throw on malformed t() calls", false)
  .action(
    (opts: { src: string; out: string; strict: boolean }) => {
      const result = walk(opts.src);
      writeJson(opts.out, result.extracted);
      process.stdout.write(
        `localebridge: ${result.extracted.length} strings from ${result.files_scanned} files -> ${opts.out}\n`,
      );
    },
  );

program.parseAsync(process.argv).catch((err: unknown) => {
  process.stderr.write(`localebridge error: ${String(err)}\n`);
  process.exit(1);
});

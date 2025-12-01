"""
Simple PyDriller Analysis - Run this to see your project metrics
Save as: run_pydriller.py
"""

from pydriller import Repository
from collections import defaultdict

print("=" * 70)
print("MOVIE REVIEW PROJECT - PYDRILLER ANALYSIS")
print("=" * 70)

# Initialize counters
total_commits = 0
authors = set()
files_changed = defaultdict(int)
total_additions = 0
total_deletions = 0
commits_by_branch = defaultdict(int)
test_files = set()

print("\nAnalyzing repository... (this may take a moment)\n")

# Analyze all commits
for commit in Repository(".").traverse_commits():
    total_commits += 1
    authors.add(commit.author.name)
    
    # Count changes per file
    for mod in commit.modified_files:
        if mod.filename:
            files_changed[mod.filename] += 1
            total_additions += mod.added_lines
            total_deletions += mod.deleted_lines
            
            # Track test files
            if 'test' in mod.filename.lower():
                test_files.add(mod.filename)

print("=" * 70)
print("OVERALL STATISTICS")
print("=" * 70)
print(f"\n📊 Total Commits: {total_commits}")
print(f"👥 Total Authors: {len(authors)}")
print(f"   Authors: {', '.join(authors)}")
print(f"\n📝 Code Changes:")
print(f"   Lines Added: {total_additions:,}")
print(f"   Lines Deleted: {total_deletions:,}")
print(f"   Net Change: {total_additions - total_deletions:,} lines")
print(f"\n🧪 Test Files: {len(test_files)}")

print("\n" + "=" * 70)
print("TOP 10 MOST MODIFIED FILES")
print("=" * 70)
sorted_files = sorted(files_changed.items(), key=lambda x: x[1], reverse=True)
for i, (filename, count) in enumerate(sorted_files[:10], 1):
    print(f"{i:2d}. {filename:50s} ({count} changes)")

print("\n" + "=" * 70)
print("BRANCH ANALYSIS")
print("=" * 70)

# Analyze specific branches from your PRs
branches_to_check = ['main', 'master', 'search_feature', 'auth_feature', 'foundation_feature']

for branch in branches_to_check:
    try:
        count = 0
        for commit in Repository(".", only_in_branch=branch).traverse_commits():
            count += 1
        if count > 0:
            print(f"✓ {branch:25s}: {count} commits")
    except:
        pass  # Branch doesn't exist, skip it

print("\n" + "=" * 70)
print("COMMITS PER CONTRIBUTOR")
print("=" * 70)

# Count commits per author
author_commits = defaultdict(int)
author_additions = defaultdict(int)
author_deletions = defaultdict(int)

for commit in Repository(".").traverse_commits():
    author_commits[commit.author.name] += 1
    for mod in commit.modified_files:
        author_additions[commit.author.name] += mod.added_lines
        author_deletions[commit.author.name] += mod.deleted_lines

# Sort by commit count
sorted_authors = sorted(author_commits.items(), key=lambda x: x[1], reverse=True)

for i, (author, commit_count) in enumerate(sorted_authors, 1):
    additions = author_additions[author]
    deletions = author_deletions[author]
    percentage = (commit_count / total_commits * 100) if total_commits > 0 else 0
    
    print(f"\n{i}. {author}")
    print(f"   Commits: {commit_count} ({percentage:.1f}% of total)")
    print(f"   Lines Added: {additions:,}")
    print(f"   Lines Deleted: {deletions:,}")
    print(f"   Net Contribution: {additions - deletions:,} lines")

print("\n" + "=" * 70)
print("TEST FILES DETECTED")
print("=" * 70)

if test_files:
    for i, test_file in enumerate(sorted(test_files), 1):
        print(f"{i:2d}. {test_file}")
else:
    print("No test files detected")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE!")
print("=" * 70)
print("\n💡 Metrics you can report:")
print(f"   • Total commits: {total_commits}")
print(f"   • Contributors: {len(authors)}")
print(f"   • Lines of code added: {total_additions:,}")
print(f"   • Test files created: {len(test_files)}")
print(f"   • Most active file: {sorted_files[0][0] if sorted_files else 'N/A'}")
print("\n✅ You can now take a screenshot or copy these results for your submission!")
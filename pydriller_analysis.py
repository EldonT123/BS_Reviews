"""
PyDriller Analysis Script for Movie Review Project
Analyzes Git repository metrics and commit patterns
"""

from pydriller import Repository
from datetime import datetime
from collections import defaultdict
import json

# ============== CONFIGURATION ==============
REPO_PATH = "."  # Current directory (or specify full path to your repo)
# REPO_PATH = "/path/to/your/movie-review-project"  # Alternative: absolute path

# ============== ANALYSIS FUNCTIONS ==============

def analyze_commits(repo_path):
    """Analyze all commits in the repository"""
    print("=" * 60)
    print("COMMIT ANALYSIS")
    print("=" * 60)
    
    commit_count = 0
    authors = set()
    files_modified = defaultdict(int)
    
    for commit in Repository(repo_path).traverse_commits():
        commit_count += 1
        authors.add(commit.author.name)
        
        # Track modified files
        for modification in commit.modified_files:
            files_modified[modification.filename] += 1
    
    print(f"\nTotal Commits: {commit_count}")
    print(f"Total Authors: {len(authors)}")
    print(f"Authors: {', '.join(authors)}")
    print(f"\nMost Modified Files:")
    
    # Show top 10 most modified files
    sorted_files = sorted(files_modified.items(), key=lambda x: x[1], reverse=True)
    for filename, count in sorted_files[:10]:
        print(f"  {filename}: {count} modifications")
    
    return commit_count, authors, files_modified


def analyze_branches(repo_path):
    """Analyze branches in the repository"""
    print("\n" + "=" * 60)
    print("BRANCH ANALYSIS")
    print("=" * 60)
    
    branches = {}
    
    # Analyze specific branches mentioned in your PRs
    branch_names = ['main', 'search_feature', 'auth_feature', 'foundation_feature']
    
    for branch in branch_names:
        try:
            commit_count = 0
            for commit in Repository(repo_path, only_in_branch=branch).traverse_commits():
                commit_count += 1
            branches[branch] = commit_count
            print(f"\nBranch: {branch}")
            print(f"  Commits: {commit_count}")
        except Exception as e:
            print(f"\nBranch: {branch} - Not found or error: {e}")
    
    return branches


def analyze_file_changes(repo_path):
    """Analyze code changes and complexity"""
    print("\n" + "=" * 60)
    print("CODE CHANGE ANALYSIS")
    print("=" * 60)
    
    total_additions = 0
    total_deletions = 0
    file_types = defaultdict(int)
    
    for commit in Repository(repo_path).traverse_commits():
        for modification in commit.modified_files:
            total_additions += modification.added_lines
            total_deletions += modification.deleted_lines
            
            # Track file types
            if modification.filename:
                ext = modification.filename.split('.')[-1] if '.' in modification.filename else 'no_ext'
                file_types[ext] += 1
    
    print(f"\nTotal Lines Added: {total_additions}")
    print(f"Total Lines Deleted: {total_deletions}")
    print(f"Net Change: {total_additions - total_deletions} lines")
    
    print(f"\nFile Types Modified:")
    sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
    for ext, count in sorted_types[:10]:
        print(f"  .{ext}: {count} files")
    
    return total_additions, total_deletions, file_types


def analyze_test_files(repo_path):
    """Analyze test file commits"""
    print("\n" + "=" * 60)
    print("TEST FILE ANALYSIS")
    print("=" * 60)
    
    test_commits = 0
    test_files = set()
    
    for commit in Repository(repo_path).traverse_commits():
        for modification in commit.modified_files:
            if modification.filename and 'test' in modification.filename.lower():
                test_commits += 1
                test_files.add(modification.filename)
    
    print(f"\nCommits Touching Test Files: {test_commits}")
    print(f"Unique Test Files: {len(test_files)}")
    
    if test_files:
        print(f"\nTest Files Found:")
        for test_file in sorted(test_files):
            print(f"  {test_file}")
    
    return test_commits, test_files


def analyze_specific_pr(repo_path, branch_name, pr_number):
    """Analyze a specific PR branch"""
    print("\n" + "=" * 60)
    print(f"PR #{pr_number} ANALYSIS: {branch_name}")
    print("=" * 60)
    
    try:
        commits = []
        files_changed = set()
        total_additions = 0
        total_deletions = 0
        
        for commit in Repository(repo_path, only_in_branch=branch_name).traverse_commits():
            commits.append({
                'hash': commit.hash[:7],
                'message': commit.msg.split('\n')[0],  # First line only
                'author': commit.author.name,
                'date': commit.author_date.strftime('%Y-%m-%d')
            })
            
            for mod in commit.modified_files:
                files_changed.add(mod.filename)
                total_additions += mod.added_lines
                total_deletions += mod.deleted_lines
        
        print(f"\nTotal Commits: {len(commits)}")
        print(f"Files Changed: {len(files_changed)}")
        print(f"Lines Added: {total_additions}")
        print(f"Lines Deleted: {total_deletions}")
        
        print(f"\nRecent Commits:")
        for commit in commits[-5:]:  # Show last 5 commits
            print(f"  {commit['hash']}: {commit['message']} ({commit['author']}, {commit['date']})")
        
        print(f"\nFiles Changed:")
        for filename in sorted(files_changed)[:20]:  # Show first 20 files
            print(f"  {filename}")
        
        return commits, files_changed
        
    except Exception as e:
        print(f"Error analyzing branch {branch_name}: {e}")
        return [], set()


def generate_metrics_report(repo_path):
    """Generate comprehensive metrics report"""
    print("\n" + "=" * 60)
    print("GENERATING COMPREHENSIVE METRICS REPORT")
    print("=" * 60)
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'repository': repo_path
    }
    
    # Run all analyses
    commit_count, authors, files_modified = analyze_commits(repo_path)
    branches = analyze_branches(repo_path)
    additions, deletions, file_types = analyze_file_changes(repo_path)
    test_commits, test_files = analyze_test_files(repo_path)
    
    # Compile metrics
    metrics['commits'] = {
        'total': commit_count,
        'authors': list(authors),
        'author_count': len(authors)
    }
    
    metrics['code_changes'] = {
        'additions': additions,
        'deletions': deletions,
        'net_change': additions - deletions
    }
    
    metrics['branches'] = branches
    
    metrics['tests'] = {
        'test_commits': test_commits,
        'test_files_count': len(test_files),
        'test_files': list(test_files)
    }
    
    metrics['file_types'] = dict(file_types)
    
    # Save to JSON
    with open('pydriller_metrics.json', 'w') as f:
        json.dump(metrics, indent=2, fp=f)
    
    print("\n✅ Metrics saved to 'pydriller_metrics.json'")
    
    return metrics


# ============== MAIN EXECUTION ==============

if __name__ == "__main__":
    print("PyDriller Analysis for Movie Review Project")
    print("=" * 60)
    
    # Run comprehensive analysis
    analyze_commits(REPO_PATH)
    analyze_branches(REPO_PATH)
    analyze_file_changes(REPO_PATH)
    analyze_test_files(REPO_PATH)
    
    # Analyze specific PRs (based on your documentation)
    print("\n\n" + "=" * 60)
    print("ANALYZING SPECIFIC PRs")
    print("=" * 60)
    
    analyze_specific_pr(REPO_PATH, 'search_feature', 1)
    analyze_specific_pr(REPO_PATH, 'auth_feature', 4)
    analyze_specific_pr(REPO_PATH, 'foundation_feature', 5)
    
    # Generate final report
    metrics = generate_metrics_report(REPO_PATH)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print("=" * 60)
    print("\nYou can now submit these metrics for your assignment.")
    print("Key metrics analyzed:")
    print("  • Commit history and author statistics")
    print("  • Branch-specific analysis")
    print("  • Code change metrics (additions/deletions)")
    print("  • Test file coverage")
    print("  • File type distribution")
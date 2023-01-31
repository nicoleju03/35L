# Keep the function signature,
# but replace its body with your implementation.
#
# Note that this is the driver function.
# Please write a well-structured implemention by creating other functions outside of this one,
# each of which has a designated purpose.
#
# As a good programming practice,
# please do not use any script-level variables that are modifiable.
# This is because those variables live on forever once the script is imported,
# and the changes to them will persist across different invocations of the imported functions.

# Keep the function signature,
# but replace its body with your implementation.
#
# Note that this is the driver function.
# Please write a well-structured implemention by creating other functions outside of this one,
# each of which has a designated purpose.
#
# As a good programming practice,
# please do not use any script-level variables that are modifiable.
# This is because those variables live on forever once the script is imported,
# and the changes to them will persist across different invocations of the imported functions.
import os
import sys
import zlib

def find_dir():
    while os.getcwd() != "/":
        dirs = os.listdir()
        for dir in dirs:
            if dir == ".git":
               # print (os.getcwd())
                return os.getcwd()
        os.chdir("..")
    sys.stderr.write("Not inside a Git repository")
    sys.exit(1)
        
#print(find_dir())

def get_branches(path = ""):
    os.chdir(find_dir())
    branches = ".git/refs/heads"
    if not os.path.isdir(branches):
        print(".git/refs/heads doesn't exist", file=sys.stderr)
        exit(1)
    branch_list = []
    # Get all files and dirs inside the branches dir                                                                                                                                              
    for root, dirs, files in os.walk(branches):
        for f in files + dirs:
            if os.path.isfile(os.path.join(root, f)):
                branch_name = os.path.join(root, f)
#                print(branch_name)
                branch_list.append(os.path.join(find_dir(), root, f))
#    print(branch_list)
    return branch_list

#get_branches()

class CommitNode:
    def __init__(self, commit_hash, branches=[]):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set() #hashes of parents
        self.children = set() #hashes of children
        self.branches = branches #need to know if commit is head of a branch
        
#return list of hashes of parents of this commit
def get_parents(hash):
    parents = set()
    dir_name = hash[:2]
    path_to_dir = os.path.join(find_dir(),".git/objects",dir_name)
    if not os.path.isdir(path_to_dir):
        sys.stderr.write(path_to_dir + "does not exist")
        sys.exit(1)
    os.chdir(path_to_dir)
    if not os.path.isfile(hash[2:]):
        sys.stderr.write(hash + " object does not exist")
        sys.exit(1)
    compressed = open(hash[2:],'rb')
    decompressed = zlib.decompress(compressed.read()).decode()
#    print(decompressed)
    compressed.close()
    for line in decompressed.split('\n'):
        if line.startswith("parent"):
            words = line.split()
            parents.add(words[1])
    parents = sorted(parents)
    return parents
    
#depth first search for one branch
def dfs(hash, commits):
    roots = set()
    s = [] #stack for commit nodes                                                       
    s.append(commits[hash]) #add the first commit for this branch
    while len(s)!=0:
        top_commit = s.pop()
        parents = get_parents(top_commit.commit_hash)
#        print(parents)
        if len(parents) == 0:
            #root commit
            roots.add(top_commit.commit_hash)
        else:
            for p in parents:
                top_commit.parents.add(p)
                #if the commit node for this parent already exists, don't need to add to stack,
                #just edit children of that parent node
                if p in commits.keys():
                    commits[p].children.add(top_commit.commit_hash)
                #if there is no commit node for this parent, add node to commits, add to stack
                else:
                    node = CommitNode(p,[])
                    commits[p] = node
                    commits[p].children.add(top_commit.commit_hash)
                    s.append(node)
    return roots

def graph():
    branches = get_branches() #returns list of branch paths
    commits = {} #dictionary to map hash to CommitNode
    root_commits = set() #set of commits with no parents (roots)
    branch_heads = set()
    for b in branches:
        if os.path.isfile(b):
            open_file = open(b)
            hash = open_file.read().rstrip('\n')
            branch_heads.add(hash)
            #if alr in commits, this commit is the head of two branches, need to update commit node branches
            if hash in commits.keys():
                index = b.find("refs/heads/")
                branch_name = b[index+11:] #getting the branch name from the path
                commits[hash].branches.append(branch_name)
#                print(branch_name)
            else:
                index = b.find("refs/heads/")
                branch_name = b[index+11:] #getting the branch name from the path
                branch_list = [branch_name]
                node = CommitNode(hash, branch_list)
                commits[hash] = node
                more_roots = dfs(hash,commits) #this will add the commits from dfs on this branch to commits
#                print(more_roots)
                root_commits = root_commits.union(more_roots)
            open_file.close()
    branch_heads = sorted(branch_heads)
    root_commits = sorted(root_commits)

    return commits, root_commits
#    print(commits)

def generate_topological_ordering(roots, commits):
    sorted_commits = []
    visited = set() #commits we've visited
    all_commits = list(roots) #start with the roots
    while len(all_commits) != 0:
        # Get the top element
        top = all_commits[len(all_commits) - 1]
        visited.add(top)
        #list of all children
        number_of_children = []
        for children in commits[top].children:
            if children not in visited:
                # add children we haven't visited yet
                number_of_children.append(children)
        # if no children, so branch head
        if len(number_of_children) == 0:
            # add to the sorted commits
            sorted_commits.append(top)
            all_commits.pop()
        else:
            # add the first child that wasn't visited
            all_commits.append(commits[number_of_children[0]].commit_hash)
    # sorted with branch heads first
    return sorted_commits

def print_hashes(sorted_commits, commits):
    sticky_start = False
    for i in range(len(sorted_commits)):
        commit = sorted_commits[i]
        if i < len(sorted_commits)-1:
            next_commit = sorted_commits[i+1]
        else:
            next_commit = None
        #sticky start
        if sticky_start:
            print("=", end="")
            print(*commits[commit].children, sep=' ')
            sticky_start = False
        if len(commits[commit].branches) == 0:
            print(commit)
        else:
            print(commit+" ", end="")
            print(*sorted(commits[commit].branches), sep=' ')
        #sticky end
        if next_commit is not None and next_commit not in commits[commit].parents:
            print(*commits[commit].parents, sep=' ', end="")
            print("=\n")
            sticky_start = True

def topo_order_commits():
#    raise NotImplementedError
    #commits, branch_heads = graph()
    #topo_sort(commits, branch_heads)
    commits, root_commits = graph()
    sorted_commits = generate_topological_ordering(root_commits, commits)
    print_hashes(sorted_commits,commits)

if __name__ == '__main__':
    topo_order_commits()

#strace -f -o topo-test.tr pytest --> said I passed 24 tests in 20.49 seconds, outputted a file topo-test.tr that did not contain any commands

#!/usr/bin/env python3
"""
n8n Workflow Compatibility Validator
Tests all workflows for n8n import readiness
"""

import json
import os
from typing import Dict, List, Any

def validate_n8n_workflow(file_path: str) -> Dict[str, Any]:
    """Validate a single n8n workflow file"""
    result = {
        "file": file_path,
        "valid": False,
        "errors": [],
        "warnings": [],
        "node_count": 0,
        "connection_count": 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # Check required top-level fields
        required_fields = ["name", "nodes", "connections"]
        for field in required_fields:
            if field not in workflow:
                result["errors"].append(f"Missing required field: {field}")
        
        # Validate nodes
        if "nodes" in workflow:
            nodes = workflow["nodes"]
            if not isinstance(nodes, list):
                result["errors"].append("'nodes' must be an array")
            else:
                result["node_count"] = len(nodes)
                
                for i, node in enumerate(nodes):
                    if not isinstance(node, dict):
                        result["errors"].append(f"Node {i} is not an object")
                        continue
                    
                    # Check required node fields
                    node_required = ["id", "name", "type", "position"]
                    for field in node_required:
                        if field not in node:
                            result["errors"].append(f"Node {i} missing field: {field}")
                    
                    # Check node type format
                    if "type" in node and not node["type"].startswith("n8n-nodes-"):
                        result["warnings"].append(f"Node {i} type '{node['type']}' may not be valid")
        
        # Validate connections
        if "connections" in workflow:
            connections = workflow["connections"]
            if not isinstance(connections, dict):
                result["errors"].append("'connections' must be an object")
            else:
                result["connection_count"] = len(connections)
        
        # Check for n8n compatibility features
        if "meta" in workflow:
            result["warnings"].append("Meta field present (good for n8n v1+)")
        
        if "settings" in workflow:
            result["warnings"].append("Settings field present (execution order specified)")
        
        # Mark as valid if no errors
        result["valid"] = len(result["errors"]) == 0
        
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid JSON: {e}")
    except FileNotFoundError:
        result["errors"].append("File not found")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {e}")
    
    return result

def main():
    """Validate all n8n workflow files"""
    print("🔍 n8n Workflow Compatibility Validator")
    print("=" * 60)
    
    workflow_dir = "n8n/workflows"
    if not os.path.exists(workflow_dir):
        print(f"❌ Workflow directory not found: {workflow_dir}")
        return False
    
    workflow_files = [f for f in os.listdir(workflow_dir) if f.endswith('.json')]
    
    if not workflow_files:
        print(f"❌ No JSON workflow files found in {workflow_dir}")
        return False
    
    print(f"Found {len(workflow_files)} workflow file(s)")
    print()
    
    all_valid = True
    results = []
    
    for file_name in workflow_files:
        file_path = os.path.join(workflow_dir, file_name)
        result = validate_n8n_workflow(file_path)
        results.append(result)
        
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        print(f"{status} {file_name}")
        print(f"   Nodes: {result['node_count']}, Connections: {result['connection_count']}")
        
        if result["errors"]:
            for error in result["errors"]:
                print(f"   ❌ Error: {error}")
        
        if result["warnings"]:
            for warning in result["warnings"]:
                print(f"   ⚠️  Warning: {warning}")
        
        if not result["valid"]:
            all_valid = False
        
        print()
    
    # Summary
    valid_count = sum(1 for r in results if r["valid"])
    print("=" * 60)
    print(f"📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"✅ Valid workflows: {valid_count}/{len(results)}")
    print(f"📝 Total nodes: {sum(r['node_count'] for r in results)}")
    print(f"🔗 Total connections: {sum(r['connection_count'] for r in results)}")
    
    if all_valid:
        print("\n🎉 ALL WORKFLOWS ARE n8n COMPATIBLE!")
        print("✅ Ready for import into n8n dashboard")
        print("✅ Follow N8N-IMPORT-GUIDE.md for instructions")
    else:
        print(f"\n⚠️  {len(results) - valid_count} workflow(s) need fixes")
        print("❌ Fix errors before importing to n8n")
    
    return all_valid

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

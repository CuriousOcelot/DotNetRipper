using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;

class Program {
  static void Main(string[] args) {
    if (args.Length < 1) {
      Console.WriteLine("Usage: program <dllPath> -m [optional Method to prepare] -l");
      return;
    }
    string dllPath = args[0];
    string methodToPrepare = null;
    bool showFullMethodLogs = false;

    for (int i = 0; i < args.Length; i++) {
      var arg = args[i];
      if (arg == "-m") {
        i++;
        methodToPrepare = args[i];  // Skip "-m:"
        Console.WriteLine("Parsing only: " + methodToPrepare);
        continue;
      }

      if (arg == "-l") {
        Console.WriteLine("Showing full method in logs.");
        showFullMethodLogs = true;
        continue;
      }
    }
    Console.WriteLine("[INFO] Loading DLL: " + dllPath);

    try {
      Assembly assembly = Assembly.LoadFrom(dllPath);
      Console.WriteLine("[INFO] DLL loaded successfully.");
      int total = 0;
      Type[] types;
      try {
        types = assembly.GetTypes();
      } catch (ReflectionTypeLoadException rtle) {
        Console.WriteLine("[ERROR] ReflectionTypeLoadException: " + rtle.Message);
        Console.WriteLine("[INFO] LoaderExceptions:");
        foreach (Exception loaderEx in rtle.LoaderExceptions) {
          Console.WriteLine("  - " + loaderEx.Message);
        }
        return;
      }

      List<Type> allAssemblyTypes = new List<Type>(assembly.GetTypes());
      foreach (Type type in allAssemblyTypes) {
        total += type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static).Length;
        total += type.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static).Length;
      }

      int count = 0;
      List<string> methodsWithoutBody = new List<string>();
      List<string> methodsFailedToPrepare = new List<string>();
      Dictionary<string, int> methodNameToToken = new Dictionary<string, int>();
      // We need to store types which extend classes as we need in generic types
      Dictionary<string, Type> typeMap = new Dictionary<string, Type>();
      //      Type[] reversedTypes = assembly.GetTypes().Reverse().ToArray();
      //      foreach (Type type in reversedTypes) {
      foreach (Type type in assembly.GetTypes()) {
        foreach (ConstructorInfo ctor in type.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)) {
          string fullPath = type.Namespace + "." + type.Name + "." + ctor.Name;  // ctor.Name is usually ".ctor"
          bool showDotsAtConsole = !(methodToPrepare != null || showFullMethodLogs);
          try {
            if ((ctor.MethodImplementationFlags & (MethodImplAttributes.ForwardRef)) != 0) {
              methodsWithoutBody.Add(fullPath);
              methodNameToToken[fullPath] = ctor.MetadataToken;
              continue;
            }

            if ((methodToPrepare == null) || (string.Equals(methodToPrepare, fullPath, StringComparison.OrdinalIgnoreCase))) {
              if (methodToPrepare != null || showFullMethodLogs) {  // string.Equals(methodToPrepare, fullPath, StringComparison.OrdinalIgnoreCase)
                Console.WriteLine("Preparing: " + fullPath + " [Constructor]" + " | " + string.Format("0x{0:X8}", ctor.MetadataToken));
                showDotsAtConsole = false;
              }
              if (!ctor.DeclaringType.IsGenericType) {
                RuntimeHelpers.PrepareMethod(ctor.MethodHandle);
              } else {
                var genericTypeParams = ctor.DeclaringType.GetGenericArguments();
                Type[] requiredBaseList = MakeGenericBaseList(genericTypeParams, allAssemblyTypes, typeMap, fullPath);
                RuntimeTypeHandle[] handleRequiredBaseList = requiredBaseList.Select(t => t.TypeHandle).ToArray();
                RuntimeHelpers.PrepareMethod(ctor.MethodHandle, handleRequiredBaseList);
              }
              count++;
            }

          } catch (Exception ex) {
            Console.WriteLine("\nFailed to prepare constructor: " + string.Format("0x{0:X8}", ctor.MetadataToken) + " | " + fullPath + " - " + ex.Message);
            Console.WriteLine(ex.ToString());
            methodsFailedToPrepare.Add(fullPath);
            methodNameToToken[fullPath] = ctor.MetadataToken;
          }
          if (showDotsAtConsole) {
            if (count != 0 && count % 100 == 0) {
              Console.WriteLine(".");
            } else {
              Console.Write(".");
            }
          }
        }

        foreach (MethodInfo method in type.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)) {
          string fullPath = type.Namespace + "." + type.Name + "." + method.Name;
          bool showDotsAtConsole = !(methodToPrepare != null || showFullMethodLogs);
          try {
            if (method.IsAbstract || (method.MethodImplementationFlags & (MethodImplAttributes.ForwardRef)) != 0) {
              methodsWithoutBody.Add(fullPath);
              methodNameToToken[fullPath] = method.MetadataToken;
              continue;
            }

            if (methodToPrepare == null || string.Equals(methodToPrepare, fullPath, StringComparison.OrdinalIgnoreCase)) {
              if (methodToPrepare != null || showFullMethodLogs) {  // string.Equals(methodToPrepare, fullPath, StringComparison.OrdinalIgnoreCase)
                Console.WriteLine("Preparing: " + fullPath + " | " + string.Format("0x{0:X8}", method.MetadataToken));
                showDotsAtConsole = false;
              }
              if (method.DeclaringType == type) {
                if (!method.IsGenericMethodDefinition) {
                  if (!method.DeclaringType.IsGenericType) {
                    RuntimeHelpers.PrepareMethod(method.MethodHandle);
                  } else {
                    var genericTypeParams = method.DeclaringType.GetGenericArguments();
                    Type[] requiredBaseList = MakeGenericBaseList(genericTypeParams, allAssemblyTypes, typeMap, fullPath);
                    RuntimeTypeHandle[] handleRequiredBaseList = requiredBaseList.Select(t => t.TypeHandle).ToArray();
                    RuntimeHelpers.PrepareMethod(method.MethodHandle, handleRequiredBaseList);
                  }
                } else {
                  var genericTypeParams = method.GetGenericArguments();
                  Type[] requiredBaseList = MakeGenericBaseList(genericTypeParams, allAssemblyTypes, typeMap, fullPath);
                  MethodInfo constructed = method.MakeGenericMethod(requiredBaseList);
                  RuntimeHelpers.PrepareMethod(constructed.MethodHandle);
                }
              }
              count++;
            }

          } catch (TargetInvocationException ex) {
            Console.WriteLine("Inner Exception: " + ex);
            Console.WriteLine("Stack Trace: " + ex);
          } catch (Exception ex) {
            Console.WriteLine("\nFailed to prepare: " + string.Format("0x{0:X8}", method.MetadataToken) + " | " + fullPath + " - " + ex.Message);
            Console.WriteLine(ex.ToString());
            methodsFailedToPrepare.Add(fullPath);
            methodNameToToken[fullPath] = method.MetadataToken;
            Console.WriteLine("Line count: " + count);
          }
          if (showDotsAtConsole) {
            if (count != 0 && count % 100 == 0) {
              Console.WriteLine(".");
            } else {
              Console.Write(".");
            }
          }
        }
      }
      Console.WriteLine("");
      Console.WriteLine("");
      Console.WriteLine(new string('*', 50));
      foreach (string method in methodsWithoutBody) {
        Console.WriteLine("Without body method: " + method + " | " + string.Format("0x{0:X8}", methodNameToToken[method]));
      }
      Console.WriteLine(new string('-', 50));
      Console.WriteLine("");
      Console.WriteLine(new string('*', 50));
      foreach (string method in methodsFailedToPrepare) {
        Console.WriteLine("Failed to prepare method: " + method + " | " + string.Format("0x{0:X8}", methodNameToToken[method]));
      }
      Console.WriteLine(new string('-', 50));
      Console.WriteLine("Total without body method count = " + methodsWithoutBody.Count);
      Console.WriteLine("Failed prepared method count = " + methodsFailedToPrepare.Count);
      Console.WriteLine("Total prepared method count = " + count);
      Console.WriteLine("");
      Console.WriteLine("Task result " + (count + methodsWithoutBody.Count) + "/" + total + " methods done.");
      Console.WriteLine("Path of the binary: " + dllPath);

    } catch (Exception ex) {
      Console.WriteLine("[ERROR] Exception: " + ex.Message);

      Exception inner = ex.InnerException;
      while (inner != null) {
        Console.WriteLine("  Inner exception: " + inner.Message);
        Console.WriteLine("  Stack trace: " + inner.StackTrace);
        inner = inner.InnerException;
      }
    }
  }

  private static Type[] MakeGenericBaseList(Type[] genericTypes, List<Type> allAssemblyTypes, Dictionary<string, Type> typeMap, string fn) {
    Type[] requiredBaseList = new Type[genericTypes.Length];
    for (int i = 0; i < genericTypes.Length; i++) {
      Type genericTypeParam = genericTypes[i];
      Type[] constraints = genericTypeParam.GetGenericParameterConstraints();

      Type requiredBase = null;

      if (constraints.Length != 0) {
        if (constraints.Length > 1) {
          var constraintsList = constraints.ToList();  // We need to resolve constraintsList to a single constraint
          requiredBase = TypeResolver(constraintsList, allAssemblyTypes, typeMap, fn);
        } else {
          requiredBase = constraints.FirstOrDefault();
        }
      }
      if (requiredBase == null) {
        requiredBase = typeof(object);
      }
      requiredBaseList[i] = requiredBase;
    }
    return requiredBaseList;
  }

  private static Type TypeResolver(List<Type> baseTypeList, List<Type> allTypeList, Dictionary<string, Type> typeMap, string fn) {
    // This will search the type which fulfill multiple constraint from the assembly
    List<Type> typeListSorted = baseTypeList.OrderBy(t => t.Name).ToList();
    string[] keyList = typeListSorted.Select(t => t.FullName).ToArray();
    string keyName = string.Join("", keyList);
    Type foundType;
    if (typeMap.TryGetValue(keyName, out foundType)) {
      Console.WriteLine("\n" + keyName + "  key is already created");
      return foundType;
    }
    foreach (Type type in allTypeList) {
      bool matchesAll = true;
      foreach (Type baseType in baseTypeList) {
        if (baseType.IsInterface) {
          if (!baseType.IsAssignableFrom(type)) {
            matchesAll = false;
            break;
          }
        } else {
          if (!type.IsSubclassOf(baseType)) {
            matchesAll = false;
            break;
          }
        }
      }

      if (matchesAll) {
        typeMap[keyName] = type;
        return type;
      }
    }
    throw new InvalidOperationException("No type found that matches all base types: " + keyName);
  }
}
